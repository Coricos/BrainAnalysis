# Author:  DINDIN Meryll
# Date:    12 August 2019
# Project: DreemHeadband

try: from stimuler.optimizer import *
except: from optimizer import *

if __name__ == '__main__':

    # Load the slurm relative configuration
    with open('srun-conf.json', 'r') as raw: cfg = json.load(raw)

    # Initialize the arguments
    prs = argparse.ArgumentParser()    
    prs.add_argument('-m', '--mod', help='ModelType', type=str, default='LGB')
    prs.add_argument('-r', '--rnd', help='RandomSte', type=int, default=42)
    prs.add_argument('-i', '--itr', help='NumTrials', type=int, default=80)
    prs = prs.parse_args()

    # Defines the command chunks
    cmd = ['nohup srun']
    for k, v in cfg.items(): cmd += ['--{}={}'.format(k, v)]
    cmd += ['python optimizer.py']
    for k, v in prs.__dict__.items(): cmd += ['--{}={}'.format(k, v)]
    cmd += ['--cpu={}'.format(cfg['cpus-per-task']), '&']

    # Launch the command
    os.system(' '.join(cmd))
