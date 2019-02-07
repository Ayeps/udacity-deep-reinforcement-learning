import os.path
import time
import re

import torch
import matplotlib.pyplot as plt
import numpy as np
from agent import Agent

def anneal_parameter(param, anneal_rate, param_min):
    return min(param * anneal_rate, param_min)



def generate_savename(agent_name, scores, print_count):
    """Generates an automatic savename for training files, will version-up as
       needed.
    """
    savename = "{}_{}_v".format(agent_name, time.strftime("%Y%m%d", time.gmtime()))

    files = [f for f in os.listdir('.') if os.path.isfile(f) and os.path.splitext(f)[1] == '.pth']
    files = [f for f in files if savename in f]
    if len(files)>0:
        ver = [int(re.search("_v(\d+)", file).group(1)) for file in files]
        ver = max(ver) + 1
    else:
        ver = 1
    eps = len(scores)
    avg_score = np.mean(scores[-print_count:])

    return "{}{}_{}eps_{:.2f}score{}".format(savename, ver, eps, avg_score, ".pth")



def save_checkpoint(agent, scores, print_count):
    """Saves the current Agent's learning dict as well as important parameters
       involved in the latest training.
    """
    agent.q.to('cpu')
    # checkpoint = {'agent_type': agent.framework,
    #               'state_size': agent.nS,
    #               'action_size': agent.nA,
    #               'state_dict': agent.q.state_dict(),
    #               'optimizer': agent.optimizer.state_dict(),
    #               'scores': scores,
    #               'hidden_layers': [layer.out_features for layer in agent.q.hidden_layers]
    #               }
    checkpoint = {'agent_type': agent.framework,
                  'state_size': agent.nS,
                  'action_size': agent.nA,
                  'state_dict': agent.q.state_dict(),
                  'optimizer': agent.optimizer.state_dict(),
                  'scores': scores
                  }
    save_name = generate_savename(agent.framework, scores, print_count)
    torch.save(checkpoint, save_name)
    print("{}\nSaved agent data to: {}".format("#"*50, save_name))

    return True



def load_checkpoint(filepath, device, args):
    """Loads a checkpoint from an earlier trained agent.
    """
    checkpoint = torch.load(filepath, map_location=lambda storage, loc: storage)

    if checkpoint['agent_type'] == 'DQN':
        agent = Agent(checkpoint['state_size'], checkpoint['action_size'], device, args)
    if checkpoint['agent_type'] == 'D2DQN':
        agent = Agent(checkpoint['state_size'], checkpoint['action_size'], device, args)
    agent.q.load_state_dict(checkpoint['state_dict'])
    agent.optimizer.load_state_dict(checkpoint['optimizer'])
    return agent



def load_filepath(use_latest, separator):
    """Prompts the user about what save to load, or uses the last modified save.
    """
    files = [str(f) for f in os.listdir('.') if os.path.isfile(f) and os.path.splitext(f)[1] == '.pth']
    if len(files) == 0:
        print("Oops! Couldn't find any save files in the current directory.")
        return None

    files = sorted(files, key=lambda x: os.path.getmtime(x))
    if use_latest:
        print("{0}Proceeding with file: {1}\n{0}".format(separator, files[-1]))
        return files[-1]
    else:
        message = ["{}. {}".format(len(files)-i, file) for i, file in enumerate(files)]
        message = '\n'.join(message)
        message = separator + message + " (LATEST)\n\nPlease choose a saved Agent training file (or: q/quit): "
        save_file = input(message)
        if save_file.lower() == "q" or save_file.lower() == "quit":
            return None
        try:
            file_index = len(files) - int(save_file)
            if file_index < 0:
                raise Exception()
            save_file = files[file_index]
            print("{0}\nProceeding with file: {1}\n{0}".format(separator, save_file))
            return save_file
        except:
            print("\nInput invalid...\n")
            load_filepath(use_latest)



def plot_scores(scores):
    """Simple graph of training data, score per episode across all episodes.
    """
    fig = plt.figure()
    ax = fig.add_subplot(111)
    plt.plot(np.arange(len(scores)), scores)
    plt.ylabel('Score')
    plt.xlabel('Episode #')
    plt.show()
    return



def print_verbose_info(sep, agent, env, args):
    """Prints extra data if --debug flag is set.
    """
    print("{}\nARGS:".format(sep))
    for arg in vars(args):
        print("{}: {}".format(arg.upper(), getattr(args, arg)))
    print("{}\nVARS:".format(sep))
    print("Device: {}".format(agent.device))
    print("Action Size: {}\nState Size: {}".format(agent.nA, agent.nS))
    print('Number of agents:', len(env.agents))
    print("Number of Episodes: {}".format(args.num_episodes))
    print("{1}\n{0}\n{1}".format(agent.q, sep))



def print_status(i_episode, scores, args, agent):
    if i_episode % args.print_count == 0:
        print("\nEpisode {}/{}, avg score for last {} episodes: {:3f}".format(
                i_episode, args.num_episodes, args.print_count, np.mean(scores[-args.print_count:])))
        if args.verbose:
            print("Epsilon: {}\n".format(agent.epsilon))



def get_runtime(start_time):
    m, s = divmod(time.time() - start_time, 60)
    h, m = divmod(m, 60)
    return  "{}h{}m{}s".format(int(h), int(m), int(s))



def print_interval(args, min, max):
    return int(np.clip(args.num_episodes/args.print_count, min, max))
