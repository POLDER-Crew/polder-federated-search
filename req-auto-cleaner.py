import argparse
import os
import re
from pathlib import Path
import logging 
import sys

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

DELETION_COMMENT = ' # req-auto-cleaner: commented for deletion'
TENTATIVE_COMMENT = ' # req-auto-cleaner: check package usage manually'

# -> {req1: [line1, line2], req2: ...}
def get_requirements(path: str) -> dict:
    result = {}
    
    with open(path, 'r') as file:
        add_prev_line = False
        line_index = 0
        for line in file.readlines():
            line_index += 1
            req_name = re.match('^[\w.-]+', line)
            if not req_name: # skip empty lines
                continue
            req_name = req_name.group(0).lower()
            
            pip_command = line.startswith('--')
            
            if pip_command:
                add_prev_line = True
            else:
                if req_name not in result:
                    result[req_name] = [line_index]
                else:
                    result[req_name].append(line_index)
                if add_prev_line:
                    result[req_name].append(line_index-1)
                    add_prev_line = False
    return result             


def get_imported_deps(project_path: str) -> list:
    result = set()
    python_files = Path(project_path).rglob('*.py')
    
    for file_path in python_files:
        if '/site-packages/' in str(file_path):
            # skip python file from installed packages
            continue
        
        with open(file_path, 'r') as file_reader:
            for line in file_reader.readlines():
                import_line = re.match('^(import|from)\s+([\w]+)', line)
                if import_line:
                    result.add(import_line.group(2).lower())
                else:
                    # no more import lines -> skip
                    break
    return result

def modify_line(line: str, prefix: str = None, suffix: str = None):
    res = line
    if prefix:
        res = prefix + res
    if suffix:
        if res.endswith('\n'):
            res = res.replace('\n', suffix + '\n')
        else:
            res = res + suffix
    return res

def delete_lines_from_file(
    path: str, 
    lines_to_delete: list, 
    tentative_lines: list, 
    delete_permanently=False
):
    lines = None
    with open(path, 'r') as f:
        lines = f.readlines()
    with open(path, 'w') as f:
        for idx, line in enumerate(lines):
            if (idx + 1) in lines_to_delete:
                if not delete_permanently:
                    f.write(modify_line(line, prefix='# ', suffix=DELETION_COMMENT))
            elif (idx + 1) in tentative_lines:
                f.write(modify_line(line, suffix=TENTATIVE_COMMENT))
            else:
                f.write(line) 

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Requirements auto-cleaner')
    parser.add_argument('project', type=str, help="Project's root path")
    parser.add_argument(
        '-r', 
        type=str, 
        help="Requirements file alternative path relative to project's root", 
        default='requirements.txt'
    )

    args = parser.parse_args()
    req_file_path = os.path.join(args.project, args.r)

    reqs = get_requirements(req_file_path)
    logging.debug('Requirements mapping:\n' + str(reqs))
    logging.info(f'Detected {len(reqs)} packages in requirement file')
    deps = sorted(get_imported_deps(args.project), key=len)
    logging.debug('Imports mapping:\n' + str(deps))
    logging.info(f'Analyzed {len(deps)} imported packages in code')
    logging.debug('-----------')

    # check lines to delete
    delete_lines = []
    tentative_lines = []
    for req, lines in reqs.items():
        if req not in deps:
            if '-' in req: # handle multi-word package names
                tentative_lines += lines
            else:
                delete_lines += lines
        else:
            deps.remove(req)

    logging.info('Deleteing the following lines: ' + str(delete_lines))
    delete_lines_from_file(req_file_path, delete_lines, tentative_lines)
    print('You are clean!!')
    print('Lines need a manual check: ' + str(tentative_lines))
