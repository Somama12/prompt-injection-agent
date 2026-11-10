"""Small separate live ablation: remove the synthetic credential value from the prompt.
Controls otherwise identical to the primary final-action protocol. No production secrets."""
import sys
from pathlib import Path
from agent.tools import SESSION_SECRET
from evaluation import one_step_study as study
from benchmark.attacks import ATTACKS


def run(directory):
    study.SYSTEM=study.SYSTEM.replace(SESSION_SECRET,'[not available to the assistant]')
    study.ATTACKS=[a for a in ATTACKS if a.target_action=='exfiltrate_secret']
    study.run(directory)

if __name__=='__main__':run(Path(sys.argv[1]))
