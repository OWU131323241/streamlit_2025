from datetime import datetime, timedelta
import streamlit as st
import json
import os
import pandas as pd
import altair as alt


def load_data():
    if not os.path.exists('data'):
        os.makedirs('data')
    if not os.path.exists('data/study_records.json'):
        with open('data/study_records.json', 'w') as f:
            json.dump({}, f)
    with open('data/study_records.json', 'r') as f:
        return json.load(f)

def save_data(data):
    with open('data/study_records.json', 'w') as f:
        json.dump(data, f, indent=4)

def load_subjects():
    if os.path.exists('data/subjects.json'):
        with open('data/subjects.json', 'r') as f:
            return json.load(f)
    return {}

def save_subjects(subjects):
    with open('data/subjects.json', 'w') as f:
        json.dump(subjects, f, indent=4)


def calculate_totals_by_subject(data, period="daily", start_date=None, end_date=None):
    rows = []
    for date_str, records in data.items():
        date = datetime.strptime(date_str, "%Y-%m-%d").date()
        if start_date and date < start_date:
            continue
        if end_date and date > end_date:
            continue

        if period == "daily":
            key = date.strftime("%Y-%m-%d")
        elif period == "weekly":
            start_of_week = date - timedelta(days=date.weekday())
            key = f"{start_of_week.strftime('%Y-%m-%d')}～"
        elif period == "monthly":
            key = date.strftime("%Y-%m")

        for record in records:
            rows.append({
                "期間": key,
                "科目": record.get("subject", "未設定"),
                "勉強時間": record["time"]
            })
    return pd.DataFrame(rows)


def display_totals(data):
    st.subheader("勉強時間の集計")

    # グラフ表示の期間をセッションに保持
    if "start_date" not in st.session_state:
        st.session_state["start_date"] = datetime.today().date() - timedelta(days=30)
    if "end_date" not in st.session_state:
        st.session_state["end_date"] = datetime.today().date()

    period = st.selectbox("表示範囲", ["日ごと", "週ごと(月～日曜日)", "月ごと"])
    start_date = st.date_input("表示開始日", st.session_state["start_date"])
    end_date = st.date_input("表示終了日", st.session_state["end_date"])
    st.session_state["start_date"] = start_date
    st.session_state["end_date"] = end_date

    period_map = {"日ごと": "daily", "週ごと(月～日曜日)": "weekly", "月ごと": "monthly"}
    df = calculate_totals_by_subject(
        data,
        period=period_map[period],
        start_date=start_date,
        end_date=end_date
    )

    if df.empty:
        st.info("データがありません")
        return

    total_hours = df["勉強時間"].sum()
    st.markdown(f"### 総勉強時間：{total_hours:.2f} 時間")

    df = df.groupby(["期間", "科目"]).sum().reset_index()
    subject_colors = st.session_state.get("subject_colors", {})

    color_scale = alt.Scale(domain=list(subject_colors.keys()), range=list(subject_colors.values()))

    chart = alt.Chart(df).mark_bar().encode(
        x=alt.X("期間:N", sort=None, axis=alt.Axis(labelAngle=0, labelFontWeight="bold")),
        y=alt.Y("勉強時間:Q"),
        color=alt.Color("科目:N", title="科目", scale=color_scale),
        tooltip=["期間", "科目", "勉強時間"]
    ).properties(width=700, height=400)

    st.altair_chart(chart, use_container_width=True)


def input_form():
    st.header("勉強時間の登録")

    date = st.date_input("日にち", datetime.today())
    col1, col2 = st.columns([1, 1])
    with col1:
        hours = st.selectbox("時間", list(range(0, 24)))
    with col2:
        minutes = st.selectbox("分", list(range(0, 60, 5)))

    selected_subject = st.selectbox("科目を選択", list(st.session_state["subjects"].keys()))
    
    if st.button("記録する"):
        study_time = hours + (minutes / 60.0)
        data = load_data()
        date_str = date.strftime("%Y-%m-%d")
        if date_str not in data:
            data[date_str] = []
        data[date_str].append({
            "time": study_time,
            "subject": selected_subject
        })
        save_data(data)
        st.success("勉強時間が記録されました！")

    st.markdown("<div style='margin:30px 0;'></div>", unsafe_allow_html=True)

    st.subheader("科目の追加")
    new_subject = st.text_input("新しい科目名")


    color_choices = {
        "赤": "#FF0000",
        "青": "#0000FF",
        "黄色": "#FFFF00",
        "緑": "#00FF00",
        "紫": "#9400D3",
        "茶色": "#8B0000",
        "オレンジ": "#FFA500",
        "グレー": "#C9CBCF",
        "ダークグリーン": "#006400",
        "ダークブルー": "#00008B"
    }


    selected_color_name = st.radio(
        "色を選んでください",
        options=list(color_choices.keys()),
        format_func=lambda name: name,
        horizontal=True
    )

    selected_color = color_choices[selected_color_name]

    st.markdown(
        f"選択中の色：<div style='width:20px;height:20px;border-radius:50%;background:{selected_color};border:1px solid #ccc'></div>",
        unsafe_allow_html=True
    )

    if st.button("科目を保存"):
        if new_subject:
            st.session_state["subjects"][new_subject] = selected_color
            st.session_state["subject_colors"] = st.session_state["subjects"]
            save_subjects(st.session_state["subjects"])
            st.success(f"「{new_subject}」を保存しました！")

    if not st.session_state["subjects"]:
        st.warning("科目を追加してください")
        return

    st.markdown("<div style='margin:30px 0;'></div>", unsafe_allow_html=True)


    st.subheader("登録済みの科目を削除")
    if st.session_state["subjects"]:
        subject_to_delete = st.selectbox("削除する科目を選んでください", list(st.session_state["subjects"].keys()))
        if st.button("科目を削除"):
            del st.session_state["subjects"][subject_to_delete]
            st.session_state["subject_colors"] = st.session_state["subjects"]
            save_subjects(st.session_state["subjects"])
            st.success(f"「{subject_to_delete}」を削除しました！")
    else:
        st.info("削除できる科目がありません")



def delete_records(data):
    st.header("記録を削除する")

    if not data:
        st.info("記録がありません")
        return

    dates_sorted = sorted(data.keys(), reverse=True)
    for date in dates_sorted:
        st.markdown(f"### {date}")
        records = data[date]
        new_records = []
        for i, record in enumerate(records):
            col1, col2, col3 = st.columns([3, 3, 1])
            with col1:
                st.write(f"科目: {record['subject']}")
            with col2:
                study_time = record['time']
                hours = int(study_time)
                minutes = int(round((study_time - hours) * 60))
                st.write(f"勉強時間: {hours}時間{minutes}分")
            with col3:
                if st.button("削除", key=f"del-{date}-{i}"):
                    continue  
                new_records.append(record)
        if new_records:
            data[date] = new_records
        else:
            del data[date]  

    save_data(data)
    st.success("削除が完了しました。ページを更新すると反映されます。")



def main():
    st.title("勉強時間記録帳")
    st.sidebar.header("メニュー")
    menu = st.sidebar.radio("選択してください", ["記録する", "集計を見る", "記録を削除する"])

    if "subjects" not in st.session_state:
        st.session_state["subjects"] = load_subjects()
    if "subject_colors" not in st.session_state:
        st.session_state["subject_colors"] = st.session_state["subjects"]

    data = load_data()

    if menu == "記録する":
        input_form()
    elif menu == "集計を見る":
        display_totals(data)
    elif menu == "記録を削除する":  
        delete_records(data)


if __name__ == "__main__":
    main()
