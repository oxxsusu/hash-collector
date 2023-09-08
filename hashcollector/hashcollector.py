import pandas as pd
import requests
import re

from tkinter import *
from PIL import ImageTk, Image
import webbrowser

# -------------------------- Crawling ---------------------------- #

"""
[주차별 해시태그 검색 제한 30개]
9/6 기준 검색내역 : 강아지, 올림픽공원맛집
9/13 기준 검색내역 : 
...
"""

data_list = []

#1. 해시태그 노드 ID 확인용 - parameter: keyword(검색어)
def get_hashtag_id(userid, token, keyword):
    base_url = "https://graph.facebook.com/v17.0/ig_hashtag_search"
    params = {
        "user_id": userid,
        "q": keyword,
        "access_token": token
    }

    response = requests.get(base_url, params=params)
    data = response.json()
    hashtag_id = data.get('data')[0].get('id')     # data 결과가 리스트 안에 들어가있어서 인덱싱[0]함
    print(f"해시태그 ID를 찾았습니다. >>>> {hashtag_id}")
    return hashtag_id

# requests에 대한 response 처리
def process_data(response):
    data = response.get('data')
    for d in range(len(data)):  # caption 항목이 없는 경우가 있음
        if data[d].get('caption'):  # 이스케이프 문자 제거
            data[d]['caption'] = re.sub(r"(\n)|(\r)", "", data[d]['caption'])
    data_list.extend(data)

# API 호출부
def get_media(userid, token, keyword, standard, page):
    """

    [미디어 크롤링 - 최신순, 인기순 탐색 가능]
    :argument keyword: 검색하고 싶은 해시태그명
    :argument standard: 검색 기준 (최신순은 recent, 인기순은 top을 입력)
    :argument page: 검색하고 싶은 페이지 수를 입력 (한 페이지당 25개의 게시글을 return)
                    검색된 결과가 page보다 작으면 검색된 만큼만 return

    """
    # 크롤링 항목 (fields) - 공통
    common_params = {
        "user_id": userid,
        "fields": "caption, children, comments_count, id, like_count, media_type, media_url, permalink, timestamp",
        "access_token": token,
        # "limit": 50
    }
    hashtag_id = get_hashtag_id(userid, token, keyword)
    base_url = f"https://graph.facebook.com/v17.0/{hashtag_id}/{standard}_media"
    response = requests.get(base_url, params=common_params).json()
    # print(response)

    # 데이터 처리
    process_data(response)

    count = 1
    # 페이징 처리
    paging = response.get('paging')
    # print(paging)
    cursors = paging.get('cursors')
    while cursors.get('after') and count < page:
        count += 1
        next_url = paging.get('next')
        next_response = requests.get(next_url).json()
        process_data(next_response)

    # .csv 처리
    df = pd.DataFrame(data_list)
    df = df.fillna('')  # 누락된 값이 있으면 빈 문자열로 fill
    df.to_csv(f'instagram-#{hashtag_id}-page-{page}-orderby-{standard}.csv')

    filename = f'instagram-#{hashtag_id}-page-{page}-orderby-{standard}.csv'
    print(f"데이터 저장을 완료했습니다.\n파일명: {filename}")
    return filename

# 실행 (검색하고 싶은 키워드, 기준, 검색할 페이지수)
# keyword = input("수집할 해시태그명 >>>> ")
# standard = input("수집 기준 (recent/top) >>>> ")
# page = int(input("수집할 페이지 수 >>>> "))
# get_media(keyword, standard, page)

def btn_open_link():
    webbrowser.open("https://spotlightwp.com/access-token-generator/")


# -------------------------- GUI ---------------------------- #

root = Tk()
root.title("#hash-collector ⓒoxxsusu")
root.geometry("500x700")

# 사용할 변수
standard = StringVar()
widgets = []            # 위젯 저장용
widget_values = []      # 위젯값 저장용
# start 버튼 클릭 event
def btn_get_values():
    # 초기 위젯값 초기화
    widget_values.clear()

    # 각 위젯에서 값 가져와서 순서대로 추가 -> user id, token, 해시태그명, 기준, 페이지수 순서
    for widget in widgets:
        widget_values.append(widget.get())

    print(f"입력받은 값 : {widget_values}")
    filename = get_media(widget_values[0], widget_values[1], widget_values[2], widget_values[3], int(widget_values[4]))

    success_label = Label(root, font=("", 30), text=f"Success! 🥳")
    result_label = Label(root, text=f"Data you requested has been saved.\n(*{filename})")
    failure_label =  Label(root, font=("", 20), text=f"⚠️ Error : Something went wrong.")

    # 예고(?) 창 먼저 지우고
    global desc
    desc.pack_forget()

    if filename:
        failure_label.pack_forget()
        success_label.pack()
        result_label.pack(pady=5)
    else:
        success_label.pack_forget()
        result_label.pack_forget()
        failure_label.pack()

# 커스텀 영역
# 상단 빈 공간
Label(root, text="", height=2).pack()

# logo
logo = Image.open("logo.png")
resized_l = logo.resize((340, 33), Image.LANCZOS)
resized_logo = ImageTk.PhotoImage(resized_l)
logo_label = Label(root, image=resized_logo)
logo_label.pack(fill="both", padx=10, pady=13)

Label(root, text="", height=2).pack()

# step 1. access token, user_id 발급
step1_desc = Label(root, anchor="w", justify="left", font=("Helvetica", 16), wraplength=450, text="1. Go to the link below to obtain the User ID and Access Token of the \"Business Account\".")
step1_desc.pack()
token_button = Button(root, text="🔗 Token Generator", padx=20, pady=10, command=btn_open_link)
token_button.pack(pady=10)

# 토큰 입력 프레임
token_frame = Frame(root, width=400, height=100)
id_label = Label(token_frame, justify="left", text="User Id: ")
id_label.grid(row=0, column=0, padx=2, pady=2)
id_entry = Entry(token_frame)
widgets.append(id_entry)
id_entry.grid(row=0, column=1, columnspan=2, pady=2, padx=2)
token_label = Label(token_frame, justify="left", text="Access Token: ")
token_label.grid(row=1, column=0, padx=2, pady=2)
token_entry = Entry(token_frame)
widgets.append(token_entry)
token_entry.grid(row=1, column=1, columnspan=2, pady=2, padx=2)
token_frame.pack()

Label(root, text="", height=1).pack()

# step 2. 크롤링 항목 입력
step2_desc = Label(root, anchor="w", justify="left", font=("Helvetica", 16), wraplength=450, text="2. Enter the #hashtag data you want to collect.")
step2_desc.pack(pady=10)
# 정보 입력 프레임
condition_frame = Frame(root, width=400, height=200)
hashtag_label = Label(condition_frame, justify="left", text="✅ Hashtag: ")
hashtag_label.grid(row=0, column=0, padx=2, pady=2)
hashtag_entry = Entry(condition_frame)
widgets.append(hashtag_entry)       # 해시태그값 가져오기
hashtag_entry.grid(row=0, column=1, columnspan=2, padx=2, pady=2)

standard_label = Label(condition_frame, justify="left", text="✅ Standard: ")
standard_label.grid(row=1, column=0, padx=2, pady=2)
standard_recent = Radiobutton(condition_frame, text="recent", variable=standard, value="recent")
standard_recent.grid(row=1, column=1, padx=2, pady=2)
standard_top = Radiobutton(condition_frame, text="top", variable=standard, value="top")
standard_top.grid(row=1, column=2, padx=2, pady=2)
widgets.append(standard)            # 기준값 가져오기

page_label = Label(condition_frame, justify="left", text="✅ Page count: ")
page_label.grid(row=2, column=0, padx=2, pady=2)
page_entry = Entry(condition_frame, width=5, justify="center")
widgets.append(page_entry)       #
page_entry.grid(row=2, column=1, columnspan=2, padx=2, pady=2)

condition_frame.pack()

start_button = Button(root, text="🏁 Start Collecting", bg="#CCBAFF", padx=20, pady=10, command=btn_get_values)
start_button.pack(pady=10)

desc = Label(root, borderwidth=1, relief="solid", text="The results will appear here...")
desc.pack()



mainloop()
root.destroy()