import pandas as pd
import os

# 데이터 관리: 강의 정보와 학교 건물 거리 정보를 다루는 파일
# 문자열로 된 시간이나 엑셀 파일을 다루기 쉽게 변환해서 저장해두는 역할

class LectureObj:
    #  딕셔너리로 된 강의 정보를 객체로 변환
    # 편리성: data['subject'] 대신 data.subject 처럼 쓸 수 있음
    def __init__(self, data_dict):
        self.subject = data_dict['subject']      # 과목명
        self.credit = int(data_dict['credit'])   # 학점 (문자 -> 숫자 변환)
        self.day = data_dict['day']              # 요일
        self.mode = data_dict['mode']            # 수업 방식 (대면/온라인)
        self.structure = data_dict['structure']  # 강의동 위치
        
        # 시간 계산의 편리성 위함: '09:00' 같은 문자 -> 540 같은 분 단위 숫자로 변환
        self.start_time = self.time_to_int(data_dict['start_time'])
        self.end_time = self.time_to_int(data_dict['end_time'])

    # 기능: "시:분" 문자열을 입력받아 분 단위 정수로 변환하는 함수
    #ex: "09:00" -> 9*60 + 0 = 540
    def time_to_int(self, time_str):
        try:
            if ":" in str(time_str):
                h, m = map(int, str(time_str).split(":"))
                return h * 60 + m  # 시간 * 60 + 분
            
            #9.5 같이 소수점으로 들어올 경우를 대비해 예외 처리
            t = float(time_str)
            h = int(t)
            m = int(round((t - h)*60))
            return h * 60 + m
        except:
            return 0 # 오류 발생 시 0 반환 (프로그램 꺼짐 방지)

    # 기능: 온라인 수업인지 확인하는 함수
    # 연산에서 온라인 수업은 이동 시간을 계산하지 않기 위해 쓰임
    def check_online(self):
        return "온라인" in self.mode

    # 디버깅시 객체를 print 하면 과목명이 나오도록 설정
    def __repr__(self):
        return f"[{self.subject}]"

class SchoolInfo:
    # 학교 이름 && 건물 간 거리 정보를 관리하는 클래스
    def __init__(self, school_name):
        self.school_name = school_name
        self.distance_matrix = None # 엑셀 데이터를 담을 변수
        self.buildings_list = []    # 건물 이름 목록
        self.read_csv_file()        # 생성되자마자 파일 읽기 시작

    # 기능: 같은 폴더 내의 CSV 파일을 읽어옴
    def read_csv_file(self):
        filename = f"{self.school_name}.csv"
        # 파일이 실제로 있는지 먼저 확인
        if os.path.exists(filename):
            try:
                # pandas 라이브러리 -> CSV를 읽음
                # 한글 깨짐 방지: 인코딩 utf-8-sig로 설정
                self.distance_matrix = pd.read_csv(filename, index_col=0, encoding='utf-8-sig')
                
                # 데이터 앞뒤에 공백이 있으면 매칭 안됨 문제 발생 가능 -> 공백 제거
                self.distance_matrix.index = self.distance_matrix.index.str.strip()
                self.distance_matrix.columns = self.distance_matrix.columns.str.strip()
                
                # 건물 목록 저장 (콤보박스에 쓰임)
                self.buildings_list = list(self.distance_matrix.columns)
            except Exception as e:
                print(f"파일 읽기 실패: {e}") # 에러: 콘솔에 출력
                self.distance_matrix = None
                self.buildings_list = []
        else:
            # 파일이 없으면 빈 상태로 둠
            self.distance_matrix = None
            self.buildings_list = []

    # 기능: 건물 목록을 반환
    def get_buildings(self):
        return self.buildings_list

    # 기능: 출발지에서 도착지까지 걸리는 시간을 표에서 찾고 반환
    def get_move_time(self, start, end):
        if start == end: return 0 # 같은 건물이면 이동시간 0분
        if not start or not end: return 0 # 정보가 없으면 0분
        if self.distance_matrix is None: return 0 # 파일 로드 실패했으면 0분
        
        try:
            # 행과 열로 값 찾기
            if start in self.distance_matrix.index and end in self.distance_matrix.columns:
                return int(self.distance_matrix.loc[start, end])
            # 순서 반대로 되어있는 경우에도 찾기
            elif end in self.distance_matrix.index and start in self.distance_matrix.columns:
                return int(self.distance_matrix.loc[end, start])
        except:
            return 0
        return 0