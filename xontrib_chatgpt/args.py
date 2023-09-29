from argparse import ArgumentParser

def _parse():
    cmd_parser = ArgumentParser(prog='chatgpt', description='Chat with OpenAI\'s ChatGPT from the command line')
    cmd_parser.set_defaults(cmd='send')
    p_group = cmd_parser.add_argument_group(title='Print')
    p_group.add_argument('-p', '--print', dest='cmd', const='print', action='store_const', help='Prints the conversation')
    p_group.add_argument('-n', type=int, default=10, help='Number of conversations to print')
    s_group = cmd_parser.add_argument_group(title='Save')
    s_group.add_argument('-s', '--save', dest='cmd', const='save', action='store_const', help='Saves the conversation')
    s_group.add_argument('-P', '--path', type=str, default='', help='Path to save the conversation. Default is $XONSH_DATA_DIR/chatgpt')
    s_group.add_argument('--name', type=str, default='', help='Name of the conversation file. Default is chatgpt')
    ps_group = cmd_parser.add_argument_group(title='Print or Save')
    ps_group.add_argument('-m', '--mode', type=str, default='color', choices=['color', 'no-color', 'json'], help='Mode to print or save the conversation. Default is color')
    cmd_parser.add_argument('text', nargs='*', default=None, help='Text to send to ChatGPT. Will be ignored when other cmd is used')

    return cmd_parser

if __name__ == '__main__':
    print(_parse('-p -s'))