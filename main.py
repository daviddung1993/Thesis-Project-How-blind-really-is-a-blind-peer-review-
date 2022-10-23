# This is a sample Python script.
import requests
# Press Shift+F10 to execute it or replace it with your code.

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    response = requests.get("https://api.semanticscholar.org/datasets/v1/release/latest")
    print(response.json())
# See PyCharm help at https://www.jetbrains.com/help/pycharm/
