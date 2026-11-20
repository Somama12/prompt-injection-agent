from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle

OUT = Path('output/pdf/figures')
OUT.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans', 'font.size':10, 'axes.spines.top':False,
 'axes.spines.right':False, 'pdf.fonttype':42, 'savefig.bbox':'tight'})
navy, teal, rust, grey = '#233D4D', '#007E80', '#A94F35', '#657078'
def save(fig, name):
    fig.savefig(OUT / (name+'.pdf'), facecolor='white')
    plt.close(fig)
def box(ax,x,y,w,h,title,body='',color=navy):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.012', linewidth=1.1,
                              facecolor='#F2F5F6',edgecolor=color))
    ax.text(x+w/2,y+h*.68,title,ha='center',va='center',weight='bold',fontsize=10,color=color)
    if body: ax.text(x+w/2,y+h*.30,body,ha='center',va='center',fontsize=8.8)
def arrow(ax,a,b,text=None):
    ax.add_patch(FancyArrowPatch(a,b,arrowstyle='-|>',mutation_scale=12,color=grey,lw=1.3))
    if text: ax.text((a[0]+b[0])/2,(a[1]+b[1])/2+.022,text,ha='center',fontsize=8,color=grey)

fig,ax=plt.subplots(figsize=(8,5.1)); ax.set(xlim=(0,1),ylim=(0,1));ax.axis('off')
box(ax,.03,.77,.27,.15,'Authorized user task','Read → summarize → email')
box(ax,.38,.77,.24,.15,'Agent loop','Model / tool steps')
box(ax,.71,.77,.26,.15,'Action controls','Allow-list / optional guard')
arrow(ax,(.30,.845),(.38,.845));arrow(ax,(.62,.845),(.71,.845))
box(ax,.71,.43,.26,.17,'Local tool registry','read_webpage · summarize\nsend_email')
arrow(ax,(.84,.77),(.84,.60))
box(ax,.03,.43,.27,.17,'External article','Synthetic fixture\nwith or without injection',rust)
ax.add_patch(Rectangle((.015,.405),.30,.22,fill=False,edgecolor=rust,ls='--',lw=1))
ax.text(.165,.38,'UNTRUSTED DATA',ha='center',color=rust,fontsize=8)
box(ax,.38,.43,.24,.17,'Read-time controls','Sanitization / hierarchy')
arrow(ax,(.30,.515),(.38,.515));arrow(ax,(.50,.60),(.50,.77))
arrow(ax,(.71,.48),(.62,.48))
box(ax,.03,.07,.27,.17,'Archived evidence','Manifest · transcript\nactions · errors · latency')
box(ax,.38,.07,.24,.17,'Evaluation','Effect / task scores\nAI review / policy replay')
box(ax,.71,.07,.26,.17,'Mock mailbox','Records actual deliveries\nNo real email transmission')
arrow(ax,(.84,.43),(.84,.24));arrow(ax,(.71,.155),(.62,.155));arrow(ax,(.30,.155),(.38,.155))

save(fig,'architecture')

fig,ax=plt.subplots(figsize=(8,3.65)); ax.set(xlim=(0,1),ylim=(0,1));ax.axis('off')
box(ax,.04,.69,.38,.23,'Balanced Groq pilot','4 attacked designs × 6 = 24\n6 clean controls; 30 valid records')
box(ax,.58,.69,.38,.23,'Interrupted Groq collection','5 attacked designs × 6 = 30\n6 clean controls; 36 valid records')
box(ax,.23,.30,.54,.22,'Match designs and remove overlap','One shared design: retain pilot observations\nExclude clean controls and one terminal provider error')
arrow(ax,(.23,.69),(.37,.52));arrow(ax,(.77,.69),(.63,.52))
ax.text(.5,.10,'8 distinct designs × 6 conditions = 48 full-agent outcomes',ha='center',weight='bold',color=teal,fontsize=11)
arrow(ax,(.5,.30),(.5,.16))
save(fig,'cohort_flow')

names=['Baseline','Sanitization','Hierarchy','Guard model','Allow-list','Combined']
fig,axes=plt.subplots(1,2,figsize=(8,3.8),sharey=True)
y=np.arange(6)
for ax,vals,title,color in [(axes[0],[1,2,0,0,0,0],'Assigned effect observed',rust),
                           (axes[1],[3,4,7,4,3,7],'Useful delivery without effect',teal)]:
    ax.barh(y,vals,color=color,height=.6)
    for i,v in enumerate(vals): ax.text(v+.12,i,f'{v}/8',va='center',fontsize=10)
    ax.set(xlim=(0,8.8),xticks=range(0,9,2),xlabel='Recorded episodes',title=title)
    ax.grid(axis='x',alpha=.13); ax.set_axisbelow(True)
axes[0].set_yticks(y,names);axes[0].invert_yaxis()
fig.tight_layout();save(fig,'security_counts')

fig,ax=plt.subplots(figsize=(8,3.7)); x=np.arange(3);w=.24
for offset,vals,label,color in [(-w,[27,3,3],'Goal-aware assigned effect',rust),(0,[21,15,21],'Useful delivery',grey),(w,[12,12,18],'Useful delivery without effect',teal)]:
    bars=ax.bar(x+offset,vals,w,label=label,color=color)
    ax.bar_label(bars,padding=2,fontsize=10)
ax.set(xticks=x,xticklabels=['No delivery gate','Existing gate','Repaired gate'],ylabel='Recorded attacked decisions (of 72)',ylim=(0,36))
ax.legend(loc='upper right',frameon=False,fontsize=9);ax.grid(axis='y',alpha=.12);ax.set_axisbelow(True)
fig.tight_layout();save(fig,'replay_counts')

fig,ax=plt.subplots(figsize=(8,3.5));names2=['Original\nparagraphs','Continuous\ntext','Bullets','HTML','JSON']; v=[1,30,20,12,10]
b=ax.bar(names2,v,color=[grey,teal,teal,teal,teal],width=.6)
ax.bar_label(b,labels=[f'{n}/30' for n in v],padding=4)
ax.set(ylim=(0,35),yticks=[0,10,20,30],ylabel='Emails mentioning the optional detail')
ax.grid(axis='y',alpha=.12);ax.set_axisbelow(True)
ax.text(.99,.96,'Battery and planned charging have identical counts',transform=ax.transAxes,ha='right',va='top',fontsize=8.7,color=grey)
fig.tight_layout();save(fig,'format_counts')

fig,ax=plt.subplots(figsize=(8,3.5));ax.set(xlim=(0,1),ylim=(0,1));ax.axis('off')
box(ax,.02,.37,.25,.24,'150 saved episodes','Exact summary-tool replay\n150 / 150 matches')
box(ax,.40,.66,.25,.23,'Battery present','In tool output: 61 episodes')
box(ax,.40,.10,.25,.23,'Battery absent','In tool output: 89 episodes')
box(ax,.77,.66,.21,.23,'Email retains it','61 / 61')
box(ax,.77,.10,.21,.23,'Email recovers it','12 / 89')
arrow(ax,(.27,.54),(.40,.77));arrow(ax,(.27,.44),(.40,.22));arrow(ax,(.65,.77),(.77,.77));arrow(ax,(.65,.22),(.77,.22))
ax.text(.69,.48,'Article also remains available\nto the agent',ha='center',fontsize=9,color=grey)
save(fig,'fidelity_trace')
print('Wrote six vector figures to',OUT)
