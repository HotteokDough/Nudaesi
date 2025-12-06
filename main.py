import customtkinter as ctk
from tkinter import messagebox, filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import json

# 만든 모듈들 불러오기
from models import SchoolInfo
from logic import ScheduleCalculator
from visualizer import ScheduleVisualizer
from ui_components import CommentBox, LectureTable, DRACULA_BG, DRACULA_FG, DRACULA_CURRENT

# 드라큘라 테마: 다크모드 + 커스텀 색상 사용 (개인적으로 좋아하는 테마)
ctk.set_appearance_mode("Dark") #색상 다크모드
ctk.set_default_color_theme("dark-blue") #기본 테마 설정

# 메인 컨트롤러: 전체 프로그램을 조율하는 클래스
class ScheduleAppUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("누대시 (Who Will Make My Timetable)") # 프로그램 제목
        self.geometry("1400x900") # 창 크기 설정
        self.current_fig = None   # 현재 그려진 그래프 저장용 변수
        self.school_info = None   # 학교 정보(거리 데이터) 저장용 변수
        
        # 시각화 담당 객체 생성
        self.visualizer = ScheduleVisualizer()

        # 그리드 레이아웃 잡기 (화면 분할: 좌3 : 우1)
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 왼쪽 패널 (테이블)
        left = ctk.CTkFrame(self, fg_color=DRACULA_BG) # 배경색 지정
        left.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # 상단 메뉴바 (학교 선택, 학점 입력 등)
        top = ctk.CTkFrame(left, fg_color="transparent")
        top.pack(fill="x", padx=5, pady=5)
        
        # 학교 선택 콤보박스
        ctk.CTkLabel(top, text="학교:", text_color=DRACULA_FG).pack(side="left")
        self.school_cb = ctk.CTkComboBox(top, values=["경기대학교", "성균관대학교"], command=self.on_school_change,
                                         fg_color=DRACULA_CURRENT, button_color="#bd93f9", border_color="#6272a4")
        self.school_cb.pack(side="left", padx=5)
        
        # 최대 학점 입력창
        ctk.CTkLabel(top, text="최대 학점:", text_color=DRACULA_FG).pack(side="left")
        self.credit_ent = ctk.CTkEntry(top, width=50, fg_color=DRACULA_CURRENT, border_color="#6272a4", text_color=DRACULA_FG)
        self.credit_ent.pack(side="left", padx=5)
        
        # 평가모드 스위치 (사용자가 원하는 케이스 검사할 때 사용)
        self.eval_var = ctk.BooleanVar(value=False)
        ctk.CTkSwitch(top, text="평가모드", variable=self.eval_var, command=self.toggle_mode,
                      text_color=DRACULA_FG, progress_color="#bd93f9").pack(side="right", padx=10)
        
        # 저장, 로드 버튼
        ctk.CTkButton(top, text="저장", width=60, command=self.save_file, fg_color="#ff79c6", hover_color="#ff92d0", text_color=DRACULA_BG).pack(side="right", padx=5)
        ctk.CTkButton(top, text="로드", width=60, command=self.load_file, fg_color="#8be9fd", hover_color="#a9f0fd", text_color=DRACULA_BG).pack(side="right", padx=5)

        # 스크롤 가능한 강의 입력 테이블 추가 (메인 입력창)
        self.table = LectureTable(left)
        self.table.pack(fill="both", expand=True, pady=5)

        # 오른쪽 패널 (결과창 & 그래프)
        right = ctk.CTkFrame(self, fg_color=DRACULA_BG)
        right.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        # 우선순위 설정 프레임
        p_frame = ctk.CTkFrame(right, fg_color="transparent")
        p_frame.pack(fill="x", pady=10)
        
        # 우선순위:
        ctk.CTkLabel(p_frame, text="우선순위 설정 (중복 자동 조정)", text_color=DRACULA_FG).pack()
        
        self.prio_cbs = []  # 콤보박스들을 담아둘 리스트
        self.prio_vars = [] #선택된 값들을 담아둘 변수 리스트
        opts = ["선택 안함", "공강 확보", "매일 등교", "오후수업 선호", "오전수업 선호", "주요과목 집중", "이동 거리 최소화"] #우선순위 후보들
        
        # 우선순위 3개 입력받기
        for i in range(3):
            var = ctk.StringVar(value="선택 안함")
            self.prio_vars.append(var)
            # 콤보박스 선택 시 중복 검사 함수(check_duplicate) 연결 (중복 선택 방지)
            cb = ctk.CTkComboBox(p_frame, values=opts, variable=var, command=lambda v, idx=i: self.check_duplicate(idx, v),
                                 fg_color=DRACULA_CURRENT, button_color="#bd93f9", border_color="#6272a4")
            cb.pack(pady=2)
            self.prio_cbs.append(cb)

        # 실행/분석 버튼 (이 버튼 누르면 연산 시작)
        ctk.CTkButton(right, text="실행 / 분석", height=40, font=("Arial",14,"bold"), command=self.run_process,
                      fg_color="#50fa7b", hover_color="#69ff94", text_color=DRACULA_BG).pack(fill="x", pady=10)
        
        # 결과 메시지 출력창 (스크롤 가능)
        self.comment = CommentBox(right, height=220)
        self.comment.pack(fill="x")

        # 그래프 이미지 저장 버튼
        ctk.CTkButton(right, text="그래프 저장", command=self.save_image,
                      fg_color="#ffb86c", hover_color="#ffc98d", text_color=DRACULA_BG).pack(fill="x", pady=5)

        # 그래프 그려질 영역 설정
        self.graph_area = ctk.CTkFrame(right, fg_color=DRACULA_BG)
        self.graph_area.pack(fill="both", expand=True, pady=10)
        
        # 초기 설정 (경기대 기준 로드)
        self.on_school_change("경기대학교")
        self.comment.show_default()

    # 학교 변경 시 건물 정보(CSV) 업데이트
    def on_school_change(self, school):
        info = SchoolInfo(school) # 학교 정보 객체 생성
        buildings = info.get_buildings() #건물 목록 가져오기
        self.school_info = info 
        self.table.update_buildings(buildings) # 테이블의 콤보박스 업데이트
        if not buildings:
            self.comment.set_text(f"[{school}] 데이터 없음. CSV 파일을 확인하세요.", is_error=True) # 선택한 학교 이름.csv 파일 읽어오는 방식 설정

    # 평가모드/입력모드 전환 스위치
    def toggle_mode(self):
        self.table.is_eval = self.eval_var.get()
        if self.eval_var.get():
            self.table.reset_selection() # 평가모드 켜면 기존 선택 초기화(한 행에 2개 이상 활성화 한 상태로 평가모드 진입하는거 방지용)
            msg = "평가모드: 초기화됨. 각 행에서 하나의 시간표를 선택하세요."
        else:
            msg = "입력모드: 자유롭게 선택 가능"
        self.comment.set_text(msg)

    # 우선순위 중복 선택 방지 (같은 거 두 번 골랐을 때: 이전 선택 '선택 안함'으로 바꿈)
    def check_duplicate(self, idx, value):
        if value == "선택 안함": return
        for i, var in enumerate(self.prio_vars):
            if i != idx and var.get() == value:
                var.set("선택 안함")

    # 입력한 데이터 저장 (JSON 파일)
    def save_file(self):
        data = {
            "school": self.school_cb.get(), "max_credit": self.credit_ent.get(),
            "priorities": [v.get() for v in self.prio_vars], "table": self.table.get_save_data()
        }
        f = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if f:
            with open(f, 'w', encoding='utf-8') as file: json.dump(data, file, ensure_ascii=False, indent=2)
            messagebox.showinfo("성공", "저장 완료")

    # 저장된 파일 불러오기
    def load_file(self):
        f = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if f:
            try:
                with open(f, 'r', encoding='utf-8') as file: data = json.load(file)
                self.school_cb.set(data.get("school", "경기대학교"))
                self.on_school_change(self.school_cb.get())
                self.credit_ent.delete(0, "end"); self.credit_ent.insert(0, data.get("max_credit", ""))
                
                #우선순위 불러오기
                for i, p in enumerate(data.get("priorities", [])):
                    if i < len(self.prio_vars): self.prio_vars[i].set(p)
                
                # 데이터 로드 방식 호출 (테이블 갱신)
                self.table.load_save_data(data.get("table", []))
                messagebox.showinfo("성공", "로드 완료")
            except Exception as e: messagebox.showerror("오류", f"로드 실패: {e}")

    # 그래프 png 형식으로 저장
    def save_image(self):
        if self.current_fig:
            f = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")])
            if f: self.current_fig.savefig(f); messagebox.showinfo("성공", "이미지 저장 완료")
        else: messagebox.showwarning("경고", "저장할 그래프가 없습니다.")
   
    # 실행 가능 조건 검사 (최대학점 입력 여부 -> 우선순위 선택 여부 -> 활성화된 강의 여부 -> 활성화된 강의 안 정보입력 여부)
    def run_process(self):
        try:
            # 최대 학점 입력 확인(숫자인지 체크, 0보다 큰 정수)
            try:
                max_cr = int(self.credit_ent.get())
                if max_cr <= 0: raise ValueError
            except: raise ValueError("최대 학점을 0보다 큰 정수로 입력해주세요.")

            # 우선순위 선택 확인
            priorities = [v.get() for v in self.prio_vars if v.get() != "선택 안함"]
            if not priorities: raise ValueError("우선순위를 하나 이상 선택해주세요.")

            # 과목명 중복 확인 (같은 이름 두 번 쓰면 막음: 한 행에서 하나씩 뽑아서 연산하는 시스템이라 다른 행에서 수업 겹치면 안됨) -> 경기대는 연강X 이 로직 선정 -> 추후 학교 확장과 동시에 연강 시스템 도입 예정
            is_uniq, uniq_msg = self.table.check_duplicate()
            if not is_uniq:
                self.comment.set_text(uniq_msg, is_error=True)
                return
            
            # 1열 학점 합계 확인 (미리 계산해보기: 입력 상에서 학점 오버하는지 체크하기 위함, 입력에서부터 모든 경우의 수 판별 && 불가능 도출하는 방식이 비효율적이라 생각 -> 첫번째 열만 판단 && 나머지 케이스 중 학점 초과하는 것은 탈락시키는 방식)
            is_ok_main, main_msg = self.table.check_total_credit(max_cr)
            if not is_ok_main:
                self.comment.set_text(main_msg, is_error=True)
                return

            #활성화된 강의 데이터 가져오기(활성화된 과목만 연산에 사용할 예정: 활성화 박스 없으면 돌릴 때마다 지웠다 썼다 해야하기 때문. 사용자 편의를 높이기 위한 장치, 비활성화 상태: 입력에 저장은 되어있지만 연산에 사용하지 않는 상태)
            lectures = self.table.get_active_data()
            if not lectures: raise ValueError("활성화된 강의가 하나도 없습니다. 'On' 체크박스를 확인해주세요.")

            # 계산기 객체 생성 및 실행
            calc = ScheduleCalculator(
                school_info=self.school_info,
                max_credit=max_cr,
                evaluation_mode=self.eval_var.get(),
                priorities=priorities,
                lectures_data=lectures
            )
            res = calc.run_calculation() # logic.py 파일에 존재하는 계산 함수에서 계산 시작

            # 결과 텍스트 출력 (성공/실패 메시지)
            self.comment.set_text("\n".join(res['feedback']), is_error=False)
            
            # 그래프 그리기
            for w in self.graph_area.winfo_children(): w.destroy() # 기존 그래프 삭제(겹침 방지)
            if res['schedule']:
                # 시각화 모듈 불러와서 그리기
                fig = self.visualizer.draw_schedule_graph(res['schedule'], self.school_info)
                self.current_fig = fig
                
                # Tkinter 화면에 그래프 띄우기
                canvas = FigureCanvasTkAgg(fig, master=self.graph_area)
                canvas.draw()
                canvas.get_tk_widget().pack(fill="both", expand=True)
            else:
                self.current_fig = None # 결과 없으면 그래프도 없음

        # 에러 발생 시 메시지 박스에 띄우기
        except ValueError as e:
            self.comment.set_text(str(e), is_error=True)
        except Exception as e:
            import traceback
            traceback.print_exc() #디버깅용 에러 출력
            self.comment.set_text(f"시스템 오류:\n{e}", is_error=True)

if __name__ == "__main__":
    app = ScheduleAppUI()
    app.mainloop()