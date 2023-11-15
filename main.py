import requests
import random
import datetime
import openai
import os

ELSEVIER_API_KEY = "key"
OPENAI_API_KEY = "sk-"
HEADERS = {
    'X-ELS-APIKey': ELSEVIER_API_KEY,
    'Accept': 'application/json'
}

openai.api_key = OPENAI_API_KEY

BASE_URL = 'https://api.elsevier.com/content/search/scopus?'
ABSTRACT_BASE_URL = 'https://api.elsevier.com/content/abstract/eid/'


def get_abstract(eid):
    abstract_url = f"{ABSTRACT_BASE_URL}{eid}"
    response = requests.get(abstract_url, headers=HEADERS)
    response.raise_for_status()
    abstract_data = response.json()

    if 'abstracts-retrieval-response' in abstract_data:
        coredata = abstract_data['abstracts-retrieval-response'].get(
            'coredata', None)
        if coredata:
            return coredata.get('dc:description', None)

    return None


def get_papers(query_arg):
    query = f'TITLE-ABS-KEY({query_arg})'
    print(f"query was set: {query}")

    search_url = f"{BASE_URL}query={query}&count=100&sort=-date&view=STANDARD"
    response = requests.get(search_url, headers=HEADERS)
    response.raise_for_status()
    search_results = response.json()

    print("search done")

    if 'search-results' in search_results and 'entry' in search_results['search-results']:
        result_list = search_results['search-results']['entry']
    else:
        print("Error: Unexpected API response")
        result_list = []

    num_papers = 30
    num_papers = min(num_papers, len(result_list))
    results = random.sample(result_list, k=num_papers)
    print("results are ready")

    return results


def send_message_to_gpt4(message):
    system = "以下の論文をもとに新たなテーマについての日本語実験計画書を書いてください．引用したものは[]で括って，論文の番号を入れてください．番号振りは記事で取り上げた順番に振り，下の入力の順番である必要はないです．使う論文は取捨選択して使わなかった論文は除外してください．テーマは自由に決めていいです．構成は『タイトル 1.目的 2.研究の背景 3.方法 4.研究計画 5.参考文献（PaperのTitleのみ）』で，2000文字以上である必要があります．だ，である口調で句読点は「，」「．」を使ってください．研究計画書は以下の項目で書いてください．"

    print("waiting openai...")
    response = openai.ChatCompletion.create(
        model="gpt-4-1106-preview",
        messages=[
            {'role': 'system', 'content': system},
            {'role': 'user', 'content': message}
        ],
        temperature=0.7,
    )
    print("response is ready")
    summary = response['choices'][0]['message']['content']

    return summary


if __name__ == "__main__":
    # x = input("query")

    x = " spatial disorientation pilot"
    query_arg = str(x)
    papers = get_papers(query_arg)
    paper_count = 1

    message = ""
    for paper in papers:
        eid = paper.get('eid', None)  # 文章のeidの取得
        abstract = get_abstract(eid) if eid else None  # 抽象とする
        title = paper['dc:title']
        if abstract is not None:
            # print(
            #     f"Paper {paper_count}:\nTitle: {title}\nAbstract: {abstract}\n")
            print(f"Paper {paper_count}")
            message += f"Paper {paper_count}:\nTitle: {title}\nAbstract: {abstract}\n\n"
            paper_count += 1

    response = send_message_to_gpt4(message)
    print(response)

    # Save the result to a text file
    current_time = datetime.datetime.now()
    timestamp = current_time.strftime('%Y%m%d%H%M%S')
    if not os.path.exists("letter"):
        os.makedirs("letter")
    output_file_name = os.path.join("letter", f"{timestamp}-summary.txt")

    with open(output_file_name, 'w') as f:
        f.write(response)
        f.write("\n")
        f.write("\n")
        f.write(message)
