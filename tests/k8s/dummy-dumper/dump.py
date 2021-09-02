import sys


def main(file_path: str):
    with open(file_path, 'w') as file:
        file.write('1\n2\n3')


if __name__ == '__main__':
    arg = sys.argv[1]  # file path
    main(arg)
