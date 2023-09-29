from argparse import ArgumentParser, Namespace

# def parse(args: str):
#     args = args.split()
#     cmd_parser = ArgumentParser(exit_on_error=False)
#     cmd_parser.set_defaults(cmd='send')
#     cmd_parser.add_argument('-f', nargs='?', default=None)
#     cmd_parser.add
#     if args[0] not in ['update', 'print', '-h', '--help']:
#         # return Namespace(cmd='send', message=args)
#         cmd_parser.add_argument('message', nargs='*', default=None)
#         return cmd_parser.parse_args(args)

#     # cmd_parser = ArgumentParser(exit_on_error=False)
#     subparsers = cmd_parser.add_subparsers(dest='cmd', required=False)
#     sub_up = subparsers.add_parser('update')
#     sub_up.add_argument('-v', '--verbose', action='store_true')
#     sub_print = subparsers.add_parser('print')
#     sub_print.add_argument('-c', '--color', action='store_true')
#     cmd_parser.add_argument('text', nargs='*', default=None)
    
#     return cmd_parser.parse_args(args)

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