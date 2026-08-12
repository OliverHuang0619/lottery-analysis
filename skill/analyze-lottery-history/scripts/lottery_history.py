#!/usr/bin/env python3
import argparse, csv, json, math, random, re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ANIMALS = "鼠牛虎兔龙蛇马羊猴鸡狗猪"
GLYPHS = {"⿏":"鼠", "⽜":"牛", "⻁":"虎", "兔":"兔", "⻰":"龙", "蛇":"蛇", "⻢":"马", "⽺":"羊", "猴":"猴", "鸡":"鸡", "狗":"狗", "猪":"猪"}
POSITIONS = ["平一","平二","平三","平四","平五","平六","特码"]

def dump(obj, path):
    text = json.dumps(obj, ensure_ascii=False, indent=2)
    if path: Path(path).write_text(text, encoding="utf-8")
    else: print(text)

def pdf_text(path):
    from pypdf import PdfReader
    return "\n".join((p.extract_text() or "") for p in PdfReader(path).pages)

def normalize_animal(s):
    return GLYPHS.get(s, s if s in ANIMALS else "")

def extract_history(path):
    p = Path(path)
    text = pdf_text(p) if p.suffix.lower() == ".pdf" else p.read_text(encoding="utf-8")
    issues = re.findall(r"(\d{3})期\(开奖时间:(\d{4}-\d{2}-\d{2})\)", text)
    if not issues: raise ValueError("未找到期号和开奖日期")
    prefix = text[:text.find(issues[0][0] + "期")]
    token_re = re.compile(r"(?<!\d)(0[1-9]|[1-4]\d)(?!\d)\s*([鼠牛虎兔龙蛇马羊猴鸡狗猪⿏⽜⻁⻰⻢⽺])")
    pairs = [(int(n), normalize_animal(a)) for n,a in token_re.findall(prefix)]
    needed = len(issues) * 7
    if len(pairs) < needed: raise ValueError(f"号码/生肖仅 {len(pairs)} 组，需要 {needed} 组")
    if len(pairs) > needed: pairs = pairs[-needed:]
    records=[]
    for i,(issue,date) in enumerate(issues):
        seven=pairs[i*7:(i+1)*7]
        records.append({"issue":issue,"date":date,"numbers":[{"position":POSITIONS[j],"number":n,"zodiac":a} for j,(n,a) in enumerate(seven)]})
    validate(records)
    return {"schema":"lottery-history/v1","source":str(p),"order":"descending","records":records}

def load_records(path):
    data=json.loads(Path(path).read_text(encoding="utf-8"))
    return data["records"] if isinstance(data,dict) else data

def validate(records):
    seen=set()
    for r in records:
        if r["issue"] in seen: raise ValueError("重复期号: "+r["issue"])
        seen.add(r["issue"]); nums=[x["number"] for x in r["numbers"]]
        if len(nums)!=7 or len(set(nums))!=7 or any(n<1 or n>49 for n in nums): raise ValueError("无效开奖行: "+r["issue"])

def newest(records):
    return sorted(records,key=lambda r:int(r["issue"]),reverse=True)

def analysis(records):
    desc=newest(records)
    allnums=[[x["number"] for x in r["numbers"]] for r in desc]
    special=[r["numbers"][6] for r in desc]
    def freq(rows): return dict(sorted(Counter(n for row in rows for n in row).items()))
    gaps={}
    for n in range(1,50): gaps[str(n)]=next((i for i,row in enumerate(allnums) if n in row),len(desc))
    return {"issues":len(desc),"latest_issue":desc[0]["issue"],"latest_date":desc[0]["date"],
      "frequency_all":freq(allnums),"frequency_recent10":freq(allnums[:10]),"frequency_recent30":freq(allnums[:30]),
      "special_frequency":dict(sorted(Counter(x["number"] for x in special).items())),"gaps":gaps,
      "odd_even":{"odd":sum(n%2 for row in allnums for n in row),"even":sum(n%2==0 for row in allnums for n in row)},
      "zodiac":dict(Counter(x["zodiac"] for r in desc for x in r["numbers"])),
      "latest_numbers":allnums[0]}

def zodiac_map(records):
    out={}
    for r in newest(records):
        for x in r["numbers"]:
            if x["number"] not in out and x.get("zodiac"): out[x["number"]]=x["zodiac"]
        if len(out)==49: break
    return out

def predict(records, seed=20260811):
    desc=newest(records); a=analysis(desc); total=len(desc)*7
    full=Counter(n for r in desc for n in [x["number"] for x in r["numbers"]]); recent=Counter(n for r in desc[:20] for n in [x["number"] for x in r["numbers"]])
    rng=random.Random(seed); scores={}
    for n in range(1,50):
        f=full[n]/max(total,1); rr=recent[n]/max(min(20,len(desc))*7,1); gap=min(a["gaps"][str(n)],20)/20
        scores[n]=0.45*f+0.40*rr+0.15*gap+rng.random()*1e-9
    chosen=[]
    for n in sorted(scores,key=scores.get,reverse=True):
        trial=chosen+[n]
        if len(trial)<=7 and sum(x%2 for x in trial)<=5 and sum(x<=24 for x in trial)<=5 and sum(x%10==n%10 for x in chosen)<2: chosen.append(n)
        if len(chosen)==7: break
    zmap=zodiac_map(desc); regular=sorted(chosen[:6])
    special_rows=[r["numbers"][6] for r in desc]; zfull=Counter(x["zodiac"] for x in special_rows); zrecent=Counter(x["zodiac"] for x in special_rows[:20])
    zgap={z:next((i for i,x in enumerate(special_rows) if x["zodiac"]==z),len(desc)) for z in ANIMALS}
    zscores={z:0.45*zfull[z]/max(len(desc),1)+0.40*zrecent[z]/max(min(20,len(desc)),1)+0.15*min(zgap[z],12)/12 for z in ANIMALS}
    ranked_z=sorted(ANIMALS,key=lambda z:(zscores[z],z),reverse=True); top_z=ranked_z[0]
    candidates=[n for n in range(1,50) if zmap.get(n)==top_z]; sfull=Counter(x["number"] for x in special_rows); srecent=Counter(x["number"] for x in special_rows[:20])
    sgap={n:next((i for i,x in enumerate(special_rows) if x["number"]==n),len(desc)) for n in range(1,50)}
    nscores={n:0.50*sfull[n]/max(len(desc),1)+0.35*srecent[n]/max(min(20,len(desc)),1)+0.15*min(sgap[n],20)/20 for n in candidates}
    ranked_n=sorted(candidates,key=lambda n:(nscores[n],n),reverse=True); special=ranked_n[0]
    regular=[n for n in regular if n!=special]
    for n in sorted(scores,key=scores.get,reverse=True):
        if n!=special and n not in regular: regular.append(n)
        if len(regular)==6: break
    regular=sorted(regular)
    return {"schema":"lottery-prediction/v2","created_at":datetime.now(timezone.utc).isoformat(),"cutoff_issue":desc[0]["issue"],"target_issue":f"{int(desc[0]['issue'])+1:03d}","method_version":"special-zodiac-first-v2","seed":seed,
      "regular":[{"number":n,"zodiac":zmap.get(n,"未知"),"score":round(scores[n],6)} for n in regular],
      "top_special_zodiac":{"zodiac":top_z,"score":round(zscores[top_z],6)},
      "ranked_special_zodiacs":[{"zodiac":z,"score":round(zscores[z],6)} for z in ranked_z[:3]],
      "special":{"number":special,"zodiac":top_z,"score":round(nscores[special],6)},
      "numbers_in_top_zodiac":[{"number":n,"zodiac":top_z,"score":round(nscores[n],6)} for n in ranked_n[:3]],
      "disclaimer":"仅供统计娱乐；随机开奖无法被可靠预测。"}

def review(pred, actual):
    pr={x["number"] for x in pred["regular"]}; pa={x["number"] for x in actual["numbers"][:6]}; ps=pred["special"]; acs=actual["numbers"][6]
    return {"cutoff_issue":pred.get("cutoff_issue"),"target_issue":pred.get("target_issue",actual["issue"]),"actual_issue":actual["issue"],"method_version":pred.get("method_version"),"prediction_created_at":pred.get("created_at"),
      "predicted_special_number":ps["number"],"actual_special_number":acs["number"],"special_number_hit":ps["number"]==acs["number"],
      "predicted_special_zodiac":ps.get("zodiac"),"actual_special_zodiac":acs.get("zodiac"),"special_zodiac_hit":ps.get("zodiac")==acs.get("zodiac"),
      "special_pick_regular_hit":ps["number"] in pa,"regular_hits":sorted(pr&pa),"regular_hit_count":len(pr&pa),
      "any_overlap":sorted((pr|{ps["number"]}) & (pa|{acs["number"]})),"special_abs_error":abs(ps["number"]-acs["number"])}

def main():
    ap=argparse.ArgumentParser(); sp=ap.add_subparsers(dest="cmd",required=True)
    e=sp.add_parser("extract"); e.add_argument("input"); e.add_argument("--out")
    a=sp.add_parser("analyze"); a.add_argument("records"); a.add_argument("--out")
    p=sp.add_parser("predict"); p.add_argument("records"); p.add_argument("--seed",type=int,default=20260811); p.add_argument("--out")
    r=sp.add_parser("review"); r.add_argument("records"); r.add_argument("prediction"); r.add_argument("--new-result",required=True); r.add_argument("--out")
    x=ap.parse_args()
    if x.cmd=="extract": obj=extract_history(x.input)
    elif x.cmd=="analyze": obj=analysis(load_records(x.records))
    elif x.cmd=="predict": obj=predict(load_records(x.records),x.seed)
    else:
        pred=json.loads(Path(x.prediction).read_text(encoding="utf-8")); nr=json.loads(Path(x.new_result).read_text(encoding="utf-8")); actual=nr["records"][0] if isinstance(nr,dict) and "records" in nr else nr
        obj=review(pred,actual)
    dump(obj,x.out)
if __name__=="__main__": main()
