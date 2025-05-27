import yaml
def main(checklist):
    with open('road.yaml','r') as file:
        data = yaml.safe_load(file)


if __name__ == "__main__":
    main('aa')
