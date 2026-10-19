"""Build the six-page cumulative midterm PDF from a frozen evidence snapshot."""
from pathlib import Path
import json
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Polygon

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/Midterm_Report_Somama_Siddiqui.pdf'
snapshot=json.loads((ROOT/'evidence/midterm_report_snapshot.json').read_text())
cells=[r['cell'] for r in snapshot['records']]
valid=[c for c in cells if c['status']=='ok']
clean=[c for c in valid if c['category']=='clean']
attacked=[c for c in valid if c['category']!='clean']
errors=[c for c in cells if c['status']!='ok']
judged=[c for c in attacked if type(c['judge_success']) is bool]
hits=sum(c['programmatic_success'] is True for c in attacked)
agree=sum(c['programmatic_success']==c['judge_success'] for c in judged)
order=['none','sanitization','instruction_hierarchy','guard_llm','allowlist','combined']
labels=dict(zip(order,['No defense','Sanitization','Instruction hierarchy','Guard LLM','Action allow-list','Combined defenses']))
NAVY=colors.HexColor('#17354A');TEAL=colors.HexColor('#008697');GRAY=colors.HexColor('#4B5E6F');PALE=colors.HexColor('#EDF3F5')
styles={
 'body':ParagraphStyle('body',fontName='Helvetica',fontSize=9.5,leading=12.5,spaceAfter=6),
 'small':ParagraphStyle('small',fontName='Helvetica',fontSize=8.2,leading=10.5,textColor=GRAY,spaceAfter=5),
 'h1':ParagraphStyle('h1',fontName='Helvetica-Bold',fontSize=13,leading=16,textColor=NAVY,spaceBefore=7,spaceAfter=7,keepWithNext=True),
 'h2':ParagraphStyle('h2',fontName='Helvetica-Bold',fontSize=10,leading=13,textColor=TEAL,spaceBefore=6,spaceAfter=4,keepWithNext=True),
 'title':ParagraphStyle('title',fontName='Helvetica-Bold',fontSize=21,leading=24.5,textColor=NAVY,spaceAfter=14),
 'table':ParagraphStyle('table',fontName='Helvetica',fontSize=8.2,leading=10.4),
 'th':ParagraphStyle('th',fontName='Helvetica-Bold',fontSize=8.2,leading=10.4,textColor=colors.white),
}
flow=[]
def p(text,style='body'): flow.append(Paragraph(text,styles[style]))
def h(text):p(text,'h1')
def sub(text):p(text,'h2')
def page():flow.append(PageBreak())
def table(headers,rows,widths):
 data=[[Paragraph(escape(str(x)),styles['th']) for x in headers]]+[[Paragraph(escape(str(x)),styles['table']) for x in r] for r in rows]
 t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),NAVY),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,PALE]),('LINEBELOW',(0,-1),(-1,-1),0.5,colors.HexColor('#C9D6DD'))]))
 flow.append(t);flow.append(Spacer(1,7))

def footer(canvas,doc):
 canvas.saveState();canvas.setFont('Helvetica',8);canvas.setFillColor(GRAY)
 canvas.drawString(48,764,'SENIOR SEMINAR II  |  CUMULATIVE MIDTERM  |  WEEKS 1-7')
 canvas.setStrokeColor(TEAL);canvas.setLineWidth(1);canvas.line(48,752,564,752)
 canvas.drawString(48,28,'Somama Siddiqui  |  Midterm progress and preliminary evaluation')
 canvas.drawRightString(564,28,str(doc.page));canvas.restoreState()

# PAGE 1
p('MIDTERM PROJECT REPORT | WEEKS 1-7','small')
p('Evaluating the Robustness of LLM-Based Autonomous Agents Against Prompt Injection Attacks in Tool-Use Scenarios','title')
p('<b>Somama Siddiqui</b><br/>Senior Seminar II · Instructor: Dr. Ning Zhang<br/>Fisk University · Reporting scope: Weeks 1-7 · October 5, 2026')
p(f'<b>Abstract.</b> This cumulative report documents the design, implementation, and initial evaluation of a tool-using language-model agent exposed to prompt injection. The project includes a Python agent, three mock tools, 24 attacks in four categories, four individual defenses, and a combined defense. Midterm updates add resumable experiments, repeated-trial support, corrected scoring, and an independent human-review workflow. All 40 automated tests pass. At the evidence cutoff, {len(clean)} clean controls and {len(attacked)} attacked episodes have completed successfully in a 30-episode Gemini Flash-Lite pilot. The clean controls completed the legitimate task; the limited attack observations do not establish a defense ranking. Full-grid execution, repeated trials, and human validation remain the principal work toward completion by Week 11.','small')
p('<b>Keywords:</b> prompt injection; autonomous agents; tool use; instruction hierarchy; guard LLM; security evaluation.','small')
h('1. Project Overview')
p('The project investigates whether malicious instructions embedded in external content can redirect an LLM-based agent away from its authorized task. The research question is how attack success varies across injection categories and defense mechanisms while holding the agent architecture and legitimate task constant.')
p('The agent reads a synthetic campus solar-array article, summarizes it, and emails the summary to an authorized recipient. An attacker controls text inside the article and attempts to redirect delivery, expose a synthetic session credential, or replace the summary with attacker-selected content. All tools are mocked: the experiment sends no real email and fetches no real webpage.')
sub('Objectives and expected outcome')
p('The objectives are to build a reproducible attack suite, implement comparable defenses, measure attack success and legitimate-task completion, and examine latency and added model calls. The expected final product is an empirical comparison supported by code, saved transcripts, tables, figures, validated labels, and a final report and presentation.')
sub('Cumulative scope and project links')
p('The report combines the proposal, the implementation described in Progress Report 1, the evaluation goals carried into Progress Report 2, and the verified midterm updates. Work is organized by milestones across Weeks 1-7 rather than assigning unsupported completion dates to individual weeks.')
p('<link href="https://github.com/Somama12/prompt-injection-agent" color="#008697">GitHub repository</link> · <link href="https://github.com/Somama12/prompt-injection-agent/tree/codex/midterm-evaluation" color="#008697">Midterm implementation branch</link><br/>Verified implementation commit: <b>1bac1e4</b>. The updates are pushed to <b>codex/midterm-evaluation</b> and have not been merged into the default branch.','small')
page()

# PAGE 2
h('2. Work Completed: Weeks 1-7')
sub('Milestone 1: Research scope and controlled environment')
p('The proposal defined an empirical security study using one agent task and roughly 20-30 injection attacks. The implementation uses a custom Python loop and Google Gemini rather than a larger agent framework. This keeps the tool boundary visible and allows each defense to change a specific part of the same workflow. The article, authorized destination, and synthetic credential are fixed across conditions.')
sub('Milestone 2: Agent loop and mock tools')
p('The agent requests a structured action or final response from Gemini, parses nested JSON, dispatches one tool call at a time, and records the interaction. The three tools are read_webpage, summarize, and send_email. The summarizer is deterministic and extractive; the mail tool appends a record to an in-memory log. Each episode retains the transcript, tool arguments and results, blocked actions, final response, elapsed time, and call counts.')
p('The loop permits at most six model steps. Invalid output triggers a formatting reminder; malformed tool arguments are rejected. Exhausted step budgets and model failures are recorded as errors. These safeguards make incomplete executions distinguishable from completed episodes in which the attack did not succeed.')
sub('Milestone 3: Benchmark construction and defense implementations')
table(['Attack category','Count','Representative attempted outcome'],[
 ['Direct instruction override','6','Replace the destination or overwrite the summary'],
 ['Role-play or jailbreak framing','6','Use a persona, story, or reward to redirect behavior'],
 ['Data exfiltration','6','Expose the synthetic credential in a tool argument'],
 ['Disguised system text','6','Impersonate privileged instructions inside the page'],
],[154,42,312])
p('Each attack has a unique identifier, payload, category, and declared target action. Content-replacement attacks also use a canary marker. The payload is inserted into the same article fixture, and an integrity test verifies all 24 attacks, six per category, and their inclusion in the poisoned page.')
table(['Condition','Implementation and purpose'],[
 ['No defense','Baseline agent with the same task and tools'],
 ['Sanitization','Delimits untrusted output and neutralizes selected fake role tags'],
 ['Instruction hierarchy','Adds instructions to treat retrieved content as data'],
 ['Guard LLM','Reviews proposed email actions before execution'],
 ['Action allow-list','Checks tool names, destination, secret exposure, and summary cues'],
 ['Combined defenses','Layers the four mechanisms; the first veto stops execution'],
],[130,378])
p('Four individual defenses satisfy the proposal; the combined condition is an additional comparison. The guard reviews email proposals only. Its unavailable or invalid verdict stops the episode before dispatch, so an infrastructure failure cannot be reported as evidence of a successful defense.','small')
page()

# PAGE 3
h('2. Work Completed: Weeks 1-7 (continued)')
sub('Milestone 4: Evaluation reliability and midterm updates')
p('The evaluation runner now saves every episode atomically and resumes by skipping completed records. A manifest records the agent and judge models, source fingerprint, attack selection, conditions, trial count, temperature, and pacing. A changed configuration or source requires a new run directory. Failed attempts are preserved when explicitly retried, and a lock prevents overlapping writers.')
p('Repeat trials and clean controls are supported. Model calls share a request limiter, transient errors are retried, and the provider\'s retry-delay hint is respected. Three consecutive episode failures pause a run. Fresh defense objects are constructed for each episode, avoiding shared state; combined-defense guard calls are now counted.')
sub('Milestone 5: Scoring repair and independent validation tooling')
p('The deterministic scorer checks executed outcomes. Recipient attacks require actual delivery to the attacker address, not a quoted address in a subject or body. Failed dispatches do not count as credential exposure. The judge must return a JSON boolean; strings such as "false" are rejected rather than converted to true. Summary and content checks remain heuristics that require human validation.')
p('A reproducible, stratified exporter creates numbered review packets with automated verdicts withheld. A human enters succeeded, blocked, or ambiguous. The scoring command reports agreement, precision, recall, and confusion counts, excluding ambiguous and unreviewed cases from binary metrics. It preserves all three verdicts and verifies that the labeled episode has not changed. No completed independent human-label study is claimed.')
sub('System architecture and experimental design')
d=Drawing(508,95)
boxes=[(0,120,'Poisoned article','24 attack definitions'),(139,113,'Gemini agent','Fixed task and loop'),(271,108,'Defense hooks','Prompt / output / action'),(398,110,'Mock tools','Logs and outcomes')]
for x,w,title,caption in boxes:
 d.add(Rect(x,43,w,43,fillColor=PALE,strokeColor=colors.HexColor('#B8C9D1'),strokeWidth=.6))
 d.add(String(x+7,69,title,fontName='Helvetica-Bold',fontSize=8.5,fillColor=NAVY));d.add(String(x+7,54,caption,fontName='Helvetica',fontSize=7,fillColor=GRAY))
 if x:
  d.add(Line(x-17,64,x-3,64,strokeColor=TEAL,strokeWidth=1));d.add(Polygon([x-3,64,x-7,67,x-7,61],fillColor=TEAL,strokeColor=TEAL))
d.add(String(0,22,'Saved episode  →  Deterministic scorer + Gemini judge  →  Human validation and analysis',fontName='Helvetica',fontSize=8.5,fillColor=NAVY))
flow.append(d)
p('<b>Figure 1.</b> Controlled evaluation pipeline. The same task, tools, and attack definitions are used across defense conditions; raw evidence is retained before aggregation.','small')
h('3. Evidence of Progress')
p('The original local history contains the agent, benchmark, defenses, and harness commits from September 15. Commit 1bac1e4 adds the midterm reliability and validation work. The regression suite expanded from 10 to <b>40 passing tests</b>; the recorded run completed in 13.80 seconds without requiring live model calls.')
table(['Evidence','Repository location'],[
 ['Agent, benchmark, and defenses','agent/; benchmark/; defenses/'],
 ['Evaluation and human-review workflow','evaluation/harness.py; scorer.py; validation.py'],
 ['Testing and execution environment','tests/; evidence/pytest.txt; evidence/environment.txt'],
 ['Protocol and completion milestones','docs/EXPERIMENT_PROTOCOL.md; PROJECT_MILESTONES.md'],
],[194,314])
page()

# PAGE 4
h('3. Evidence of Progress (continued)')
p(f'<b>Evidence cutoff:</b> {escape(snapshot["as_of"])}. This report uses a frozen snapshot of the ongoing pilot, not the planned total. The pilot uses <b>gemini-3.1-flash-lite</b> for the agent, guard, and judge, temperature 0, one trial, and one selected attack per category. Its planned size is 24 attacked episodes plus six clean controls.','small')
sub('Table 1. Observed clean-control results')
rows=[]
for name in order:
 c=next((x for x in clean if x['defense']==name),None)
 rows.append([labels[name], '1/1' if c and c['legitimate_success'] else '0/1' if c else 'Pending', f"{c['latency_s']:.2f}" if c else 'N/A', str(c['guard_calls']) if c else 'N/A'])
table(['Condition','Task success','Episode seconds','Guard calls'],rows,[192,94,118,104])
p('All six observed clean controls completed the legitimate task. One control per condition demonstrates feasibility; it does not estimate a reliable completion probability or prove that the defenses preserve utility under diverse inputs.')
sub('Table 2. Attack observations available at the cutoff')
rows=[]
for name in order:
 cs=[c for c in attacked if c['defense']==name]
 rows.append([labels[name],str(len(cs)),f"{sum(c['programmatic_success'] is True for c in cs)}/{len(cs)}" if cs else 'Pending',f"{sum(c['judge_success'] is True for c in cs)}/{sum(type(c['judge_success']) is bool for c in cs)}" if cs else 'Pending'])
table(['Condition','Valid attacks','Scorer successes','Judge successes'],rows,[192,86,115,115])
attack_ids=', '.join(sorted({c['attack_id'] for c in attacked})) or 'none'
p(f'The snapshot contains <b>{len(attacked)} completed attacked episodes</b> ({escape(attack_ids)}), with {hits} observed attack successes. The judge and deterministic scorer agree on {agree}/{len(judged)} available judge verdicts. This is automated agreement, not validation against a human labeler. Conditions without an observation remain pending; they are not assigned a zero success rate.')
sub('Figure 2. Observed clean-control episode time')
d=Drawing(508,113)
for i,name in enumerate(order):
 c=next((x for x in clean if x['defense']==name),None)
 y=96-i*16
 d.add(String(0,y,labels[name],fontName='Helvetica',fontSize=8.3,fillColor=NAVY))
 if c:
  w=c['latency_s']/50*290
  d.add(Rect(145,y-2,w,10,fillColor=TEAL,strokeColor=None))
  d.add(String(152+w,y,f"{c['latency_s']:.2f} s",fontName='Helvetica',fontSize=8,fillColor=NAVY))
flow.append(d)
p('Each bar is one observed episode. Timing includes agent and guard calls, request pacing, and provider retries; the later judge pass is excluded. Variations in service behavior and run order prevent interpreting these bars as isolated defense overhead.','small')
p(f'<b>Coverage and limits.</b> {len(cells)}/30 pilot episodes are saved at this cutoff; {len(errors)} saved pilot episodes are marked as errors. The full 144-cell grid, repeated trials, and human validation are incomplete. No general defense ranking is supported.','small')
page()

# PAGE 5
h('4. Progress Compared with the Original Proposal')
p('The approved proposal calls for a small Python agent, roughly 20-30 attacks, three to four candidate defenses, repeated experiments, a 30-50-run human validation sample, and an analysis of security and usability. The implementation follows that scope. The proposal does not specify dated weekly deadlines, so schedule status is assessed against the explicit Week 7 midterm and Week 11 completion targets.')
table(['Planned component','Current status','Change or qualification'],[
 ['Small agent with two to three tools','Implemented and live-tested','Custom Gemini loop; three mocked tools'],
 ['About 20-30 prompt injections','24 attacks implemented','Four categories, six attacks each'],
 ['Three to four defenses','Four plus a composite','Baseline retained for comparison'],
 ['Repeated attack-defense trials','Runner implemented; study incomplete','Pilot is one trial over four attacks'],
 ['Human validation of 30-50 runs','Workflow implemented; labels pending','Pilot alone supplies at most 24 attacked episodes'],
 ['Success, utility, and latency analysis','Preliminary observations','Full tables and comparative conclusions pending'],
 ['Final report and presentation','Planned for Week 11','Midterm summarizes implementation and pilot evidence'],
],[145,163,200])
p('The main research question is unchanged. Changes include adding a combined defense, checkpointed execution, error-aware denominators, and a verdict-blinded review workflow. These changes improve reproducibility without increasing the legitimate task\'s scope. Model availability and quota affect execution speed, so different model runs remain separate.')
p('Software implementation is ahead of experimental validation. The full grid and label sample carried over from the progress reports are still incomplete. The Week 11 target remains the working schedule, with Weeks 8-9 allocated to execution and labeling rather than assuming those tasks are already finished.')
h('5. Challenges and Solutions')
sub('API availability and account-specific quotas')
p('Live checks produced temporary service errors, and a Gemini 2.5 endpoint rejected generation despite appearing in the model listing. Gemini 3.6 completed a clean run but returned a five-request-per-minute free-tier limit. The pilot uses the previously configured Gemini 3.1 Flash-Lite in its own directory. Request pacing, bounded retries, provider retry hints, and resumable records reduce lost work. Availability and quota remain constraints.')
sub('False positives and incomplete executions')
p('Earlier scoring could interpret an attacker address quoted in a body as actual delivery, and error records could enter aggregate results as unsuccessful attacks. The scorer now checks real mock destinations, excludes failed dispatches, and reports episode errors separately. Tests cover these regressions. Heuristic content and task checks remain unresolved until independent review.')
sub('Evidence continuity and honest validation')
p('Progress Report 2 described batching and partial human review, but the supplied code did not contain a resumable runner or the human-label workflow. These features are now implemented. The midterm distinguishes that completed implementation from the still-pending labeled sample, rather than treating earlier narrative statements as validated experimental evidence.')
page()

# PAGE 6
h('6. Current Project Status')
p('The project has a complete midterm implementation: a fixed agent environment, 24-attack suite, six experimental conditions, resumable and repeatable execution, automated scorers, result generation, and an independent human-validation workflow. Forty tests pass, the code is on GitHub, and all six observed clean controls complete the assigned task.')
p(f'The live attack evaluation remains preliminary. At the cutoff, {len(attacked)} attacked episodes have finished in the balanced pilot; the full 24-attack comparison has not been completed. The main remaining work is collecting valid observations, reviewing them independently, and turning them into supported conclusions. No human agreement, precision, or recall result is reported before human labels exist.')
sub('Midterm completion target')
p('The target is <b>70% of the whole project at midterm</b> and <b>100% by Week 11</b>. Under the project\'s planning weights, research design, implementation, and software verification account for 55%; the completed pilot and preliminary analysis add 10%; the cumulative report adds 5%. These are planning estimates, not an instructor grading formula. Because the pilot is still running at the cutoff, this report does not certify that the full 70% milestone has been reached.')
p('Interpretation is limited by a small hand-authored suite, one synthetic article, one tool-use task, one pilot trial, and a shared model family for agent, guard, and judge. Repeated trials will measure variability but will not create new independent attack designs. Credential exposure is measured inside mock tool arguments, not as real network exfiltration.')
h('7. Plan for the Second Half of the Semester')
p('Remaining work is scheduled to finish by <b>Week 11</b>. Core evaluation and validation take priority over optional expansion to additional attacks or models.')
table(['Target period','Tasks and milestone','Evidence to produce'],[
 ['Week 8','Complete the first full 144-cell attack grid and six clean controls; inspect errors and export a stratified human-review sample.','Saved transcripts, coverage and error counts, initial category-by-defense table'],
 ['Week 9','Complete three trials in total: 432 attacked episodes and 18 clean controls. Finish 30-50 independent human labels.','Repeat results; labeled sample; agreement, precision, recall and ambiguity counts'],
 ['Week 10','Analyze security, task completion and observed latency. Review scorer disagreements and document limitations.','Verified tables and figures; failure-case analysis; interpretation of trade-offs'],
 ['Week 11','Finalize and verify the research report, presentation, demonstration, code and reproducibility instructions.','Final repository, traceable evidence, report and presentation'],
],[72,265,171])
p('If quota delays persist, continue from saved checkpoints and disclose actual coverage. Optional additions, such as six more attacks or a second model, follow the core study and must not displace the promised final deliverables. Independent human labels must be supplied by a reviewer, not generated and represented as human judgments.')
sub('Evidence sources')
p('Assignment 01 and Assignment 02 project proposal; Progress Reports 1 and 2; GitHub branch codex/midterm-evaluation, commit 1bac1e4; evidence/pytest.txt; docs/EXPERIMENT_PROTOCOL.md; docs/PROJECT_MILESTONES.md; results/midterm_pilot/manifest.json and episode records; frozen report snapshot evidence/midterm_report_snapshot.json.','small')
p('Report preparation date: October 5, 2026. Live execution can continue after the frozen cutoff; later observations are not silently included in these tables.','small')

OUT.parent.mkdir(exist_ok=True)
doc=SimpleDocTemplate(str(OUT),pagesize=(612,792),leftMargin=54,rightMargin=50,topMargin=60,bottomMargin=49,title='Midterm Project Report Weeks 1-7',author='Somama Siddiqui')
doc.build(flow,onFirstPage=footer,onLaterPages=footer)
print(OUT)
