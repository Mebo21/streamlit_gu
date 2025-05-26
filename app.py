import streamlit as st
import pandas as pd
import numpy as np
import requests
import io
import datetime


# Streamlit 앱 전체 설정
st.set_page_config(page_title="WattMap", layout="wide")

# ----------------------------
# 사이드바 설정
# ----------------------------
with st.sidebar:
    st.markdown("<h1 style='font-size: 30px; color: #FFFFFF;'>🔋 WattMap</h1>", unsafe_allow_html=True)
    st.markdown("---")
    if st.button("⚡ 전력 예측", use_container_width=True):
        st.session_state.page = "predict"

    # if st.button("📈 모델 정보", use_container_width=True):
    #     st.session_state.page = "model_info"

# ----------------------------
# 세션 상태 초기화
# ----------------------------
if 'page' not in st.session_state:
    st.session_state.page = "predict"  # 초기 페이지는 메인

# ----------------------------
# 전력 예측 페이지
# ----------------------------
def predict_page():
    import io

    st.title("⚡ 전력 예측 페이지")

    # 파일 업로드 영역
    st.subheader("📂 예측 파일 업로드")
    uploaded_file = st.file_uploader("CSV 파일을 업로드하세요", type=["csv"])

    if uploaded_file is not None:
        st.success("✅ 파일 업로드 완료!")
        st.markdown(f"**업로드된 파일 이름:** `{uploaded_file.name}`")

        # 파일 내용을 미리 읽어서 저장 (재사용 가능하도록)
        file_bytes = uploaded_file.read()

        try:
            df = pd.read_csv(io.StringIO(file_bytes.decode("utf-8")))
            st.dataframe(df.head(10))  # 상위 10개 행 출력
        except Exception as e:
            st.error(f"❌ CSV 읽기 오류: {str(e)}")
            return

        # 실행 버튼
        if st.button("🚀 실행", use_container_width=True):
            with st.spinner("예측을 요청 중입니다..."):
                url = 'https://port-0-gu-ai-pn2llx5u8tfw.sel5.cloudtype.app/model/predict'

                try:
                    # API 요청
                    files = {'file': (uploaded_file.name, file_bytes, uploaded_file.type)}
                    response = requests.post(url, files=files)

                    if response.status_code == 200:
                        st.success("✅ 예측 성공!")

                        st.session_state.prediction_result = response.content
                        st.session_state.page = "result"
                        st.rerun()
                    else:
                        st.error(f"❌ 서버 오류 발생: {response.text}")

                except Exception as e:
                    st.error(f"❌ 예외 발생: {str(e)}")
    else:
        st.info("📄 예측에 사용할 CSV 파일을 업로드해주세요.")


# ----------------------------
# 결과 페이지
# ----------------------------
def result_page():
    import io
    import pandas as pd

    st.title("📊 예측 결과 페이지")

    if 'prediction_result' not in st.session_state:
        st.warning("⚠ 예측 결과가 없습니다. 먼저 예측을 실행하세요.")
        return

    # 다운로드 버튼
    st.download_button(
        label="📥 예측 결과 다운로드",
        data=st.session_state.prediction_result,
        file_name="result.csv",
        mime="text/csv"
    )

    # CSV 읽기
    try:
        df_result = pd.read_csv(io.StringIO(st.session_state.prediction_result.decode('utf-8')))
    except Exception as e:
        st.error(f"CSV 읽기 실패: {str(e)}")
        return

    if 'num_date_time' not in df_result.columns or 'answer' not in df_result.columns:
        st.error("컬럼 'num_date_time' 또는 'answer'가 누락되었습니다.")
        return

    # 그룹 ID 추출 (문자열 → 숫자형 변환 포함)
    df_result['group_id'] = df_result['num_date_time'].str.extract(r'^(\d+)_')[0]
    df_result['group_id'] = pd.to_numeric(df_result['group_id'], errors='coerce')  # 숫자형으로 변환

    # 고유 그룹 오름차순 정렬
    unique_groups = sorted(df_result['group_id'].dropna().unique())

    # 그룹 선택 UI
    selected_group = st.selectbox("🔘 건물ID를 선택하세요", unique_groups)


    # 선택된 그룹의 데이터 추출 및 정렬
    group_df = df_result[df_result['group_id'] == selected_group].copy()
    group_df = group_df.sort_values('num_date_time')

    # 그래프
    st.subheader(f"📈 건물 {selected_group} 예측 결과 그래프")
    chart_data = group_df[['num_date_time', 'answer']].set_index('num_date_time')
    st.line_chart(chart_data)

    # 테이블
    st.subheader(f"📋 건물 {selected_group} 상세 데이터")
    st.dataframe(group_df.reset_index(drop=True))



# # ----------------------------
# # 모델 정보 페이지
# # ----------------------------
# def model_info_page():
#     st.title("📈 모델 정보 페이지")

#     st.subheader("📊 모델 평가 지표")
#     st.markdown("_모델 성능을 시각화한 그래프와 수치를 여기에 보여줍니다._")

#     st.line_chart(pd.DataFrame(np.random.randn(10, 3), columns=["MAE", "RMSE", "MAPE"]))

# ----------------------------
# 페이지 라우팅
# ----------------------------
if st.session_state.page == "result":
    result_page()
elif st.session_state.page == "predict":
    predict_page()
# elif st.session_state.page == "model_info":
#     model_info_page()
