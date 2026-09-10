import { mkdir, readFile, readdir, writeFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
const projectRoot = path.resolve(here, '..', '..')
const output = path.join(projectRoot, 'dashboard', 'public', 'dashboard.json')
const json = async file => JSON.parse(await readFile(path.join(projectRoot, file), 'utf8'))

async function dashboardData() {
  const [recordsDoc, analysis, evaluation, reviewFiles, predictionFiles] = await Promise.all([
    json('data/current/records.json'),
    json('data/current/analysis.json'),
    json('data/current/model-evaluation.json'),
    readdir(path.join(projectRoot, 'reviews')),
    readdir(path.join(projectRoot, 'predictions')),
  ])
  const predictionCandidates = predictionFiles
    .map(name => ({ name, match: name.match(/^prediction-for-(\d+)(-with-flat-zodiac)?\.json$/) }))
    .filter(row => row.match)
    .sort((a, b) => Number(a.match[1]) - Number(b.match[1]) || Number(Boolean(a.match[2])) - Number(Boolean(b.match[2])))
  if (!predictionCandidates.length) throw new Error('No canonical prediction file found')
  const prediction = await json(`predictions/${predictionCandidates.at(-1).name}`)
  const reviewRows = await Promise.all(reviewFiles.filter(name => /^review-.*\.json$/.test(name)).map(name => json(`reviews/${name}`)))
  const canonical = new Map()
  for (const row of reviewRows.sort((a, b) => Number(Boolean(a.correction_of)) - Number(Boolean(b.correction_of)))) canonical.set(row.actual_issue, row)
  const recordByIssue = new Map(recordsDoc.records.map(row => [row.issue, row]))
  const reviews = await Promise.all([...canonical.values()].map(async row => {
    let savedPrediction = null
    try { savedPrediction = await json(`predictions/prediction-for-${row.actual_issue}-with-flat-zodiac.json`) }
    catch { try { savedPrediction = await json(`predictions/prediction-for-${row.actual_issue}.json`) } catch { /* older review without a saved prediction file */ } }
    return { ...row, predicted_regular: savedPrediction?.regular ?? [], predicted_regular_three: savedPrediction?.regular_three ?? [], actual_numbers: recordByIssue.get(row.actual_issue)?.numbers ?? [] }
  }))
  reviews.sort((a, b) => Number(b.actual_issue) - Number(a.actual_issue))
  return { generatedAt: new Date().toISOString(), records: recordsDoc.records, analysis, prediction, evaluation, reviews }
}

await mkdir(path.dirname(output), { recursive: true })
await writeFile(output, `${JSON.stringify(await dashboardData())}\n`, 'utf8')
console.log(`Generated ${path.relative(projectRoot, output)}`)
