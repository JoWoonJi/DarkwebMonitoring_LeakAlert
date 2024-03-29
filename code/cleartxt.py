
with open('requirements.txt', 'r') as file:
    lines = file.readlines()

clean_lines = [line.split('==')[0] if '==' in line else line.split(' @ ')[0] for line in lines]

with open('requirements_no_versions.txt', 'w') as file:
    file.writelines(line + '\n' for line in clean_lines)
