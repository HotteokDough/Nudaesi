# ui_components.py
# 화면에 보이는 버튼, 입력창, 스크롤 박스 등 만드는 파일
# 메인 코드가 너무 길어짐 -> 분리

import customtkinter as ctk
from tkinter import messagebox

#  드라큘라 테마 색상 정의
DRACULA_BG = "#282a36"       # 배경
DRACULA_FG = "#f8f8f2"       # 글자
DRACULA_CURRENT = "#44475a"  # 선택된 줄
DRACULA_COMMENT = "#6272a4"  # 테두리
DRACULA_CYAN = "#8be9fd"     # 로드 버튼
DRACULA_GREEN = "#50fa7b"    # 추가 버튼
DRACULA_ORANGE = "#ffb86c"   # 그래프 저장 버튼
DRACULA_PINK = "#ff79c6"     # 체크박스
DRACULA_PURPLE = "#bd93f9"   # 스크롤바
DRACULA_RED = "#ff5555"      # 삭제 버튼

# 부모 클래스: 스크롤 기능이 필요한 모든 프레임의 부모
# 상속 사용 -> 매번 스크롤 코드 복붙 방지
class BaseScrollableFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        # 격자무늬 레이아웃 설정 (꽉 차게 늘어나도록)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 캔버스 생성: 스크롤 가능 && 도화지 역할
        # 배경색 드라큘라 테마로 설정
        self.canvas = ctk.CTkCanvas(self, highlightthickness=0, bg=DRACULA_BG)
        
        #스크롤바 생성 (세로,가로) 및 캔버스 연결
        self.v_scroll = ctk.CTkScrollbar(self, orientation="vertical", command=self.canvas.yview, fg_color=DRACULA_BG, button_color=DRACULA_PURPLE)
        self.h_scroll = ctk.CTkScrollbar(self, orientation="horizontal", command=self.canvas.xview, fg_color=DRACULA_BG, button_color=DRACULA_PURPLE)
        
        # 캔버스 -> 스크롤바 설정
        self.canvas.configure(yscrollcommand=self.v_scroll.set, xscrollcommand=self.h_scroll.set)

        # 화면에 배치(Grid 사용)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.v_scroll.grid(row=0, column=1, sticky="ns")
        self.h_scroll.grid(row=1, column=0, sticky="ew")

        # 캔버스 안에 들어갈 내용물 프레임(버튼 등)
        self.scroll_content = ctk.CTkFrame(self.canvas, fg_color=DRACULA_BG) # 배경색 통일
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scroll_content, anchor="nw")

        # 내용물 크기가 바뀜 -> 스크롤 영역도 다시 계산
        self.scroll_content.bind("<Configure>", self.resize_content)
        
        # 버튼이나 입력창 위에서는 스크롤이 안 먹히는 문제 발생
        # -> 재귀 함수 사용: 모든 자식 위젯을 찾고, 마우스 휠 이벤트를 연결
        self.connect_wheel(self.canvas)
        self.connect_wheel(self.scroll_content)

    # 내용물이 늘어나면(과목 추가 등) 스크롤 영역을 다시 계산
    def resize_content(self, event):
        self.scroll_content.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    #재귀 함수: 위젯 하나하나에 마우스 휠 이벤트를 직접 연결
    def connect_wheel(self, widget):
        widget.bind("<MouseWheel>", self.do_scroll) # 윈도우용
        widget.bind("<Button-4>", self.do_scroll)   # 리눅스용 (위로)
        widget.bind("<Button-5>", self.do_scroll)   # 리눅스용 (아래로)
        
        # 재귀 호출
        for child in widget.winfo_children():
            self.connect_wheel(child)

    # 실제 스크롤 동작 수행하는 함수
    def do_scroll(self, event):
        if self.canvas.winfo_exists():
            try:
                if event.delta: # 윈도우는 delta 값으로 방향 판단
                    self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
                elif event.num == 4: # 리눅스 위로
                    self.canvas.yview_scroll(-1, "units")
                elif event.num == 5: # 리눅스 아래로
                    self.canvas.yview_scroll(1, "units")
            except: pass
        return "break" # 이벤트가 딴 데로 새지 않게 막음 (충돌 방지)


# UI 기능 담당 부품: 개별 기능을 담당하는 작은 클래스들

class CommentBox(ctk.CTkTextbox):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        # 텍스트 박스 색상 드라큘라 테마로 변경
        self.configure(state="disabled", font=("Arial", 12), 
                       fg_color=DRACULA_CURRENT, text_color=DRACULA_FG)
        
        # 안내 메시지
        self.default_msg = (
            "[누대시: 누가 대신 시간표 짜줬으면 좋겠다]\n\n"
            "1. [학교 선택] CSV 파일을 불러와 건물 정보 로드\n"
            "2. [최대 학점] 이번 학기 제한 학점 입력\n"
            "3. [강의 입력] 'On' 체크 후 과목 정보 빈칸 없이 입력\n"
            "   (Tip: 우측 상단 'x' 버튼 -> 해당 칸 초기화)\n"
            "4. [우선순위] 추천 모드 사용 시 필수 선택 (중복 시 자동 조정)\n"
            "5. [평가 모드] 직접 짠 시간표 검증 (각 행 1개씩 선택)\n\n"
            "<그래프 이동시간 색상 안내>\n"
            "   - [회색]: 여유로움 (천천히 이동 가능)\n"
            "   - [주황]: 서둘러야 함 (1분 이내 차이)\n"
            "   - [빨강]: 이동 불가 (물리적으로 불가능)\n\n"
            "-> 입력 후 [실행 / 분석] 버튼을 눌러주세요."
        )
        self.show_default()

    # 텍스트 박스 내용 갱신하는 함수(결과/오류 출력용)
    def set_text(self, text, is_error=False):
        self.configure(state="normal") # 수정 가능하게 품
        self.delete("1.0", "end")      # 기존 내용 지움
        prefix = "[오류 발생]\n" if is_error else "[분석 결과]\n"
        self.insert("end", prefix + text) # 새 내용 입력
        self.configure(state="disabled") # 다시 잠금

    # 초기 메시지로 복구하는 함수
    def show_default(self):
        self.configure(state="normal")
        self.delete("1.0", "end")
        self.insert("end", self.default_msg)
        self.configure(state="disabled")


class LectureCell(ctk.CTkFrame):
    # 강의 입력용 네모난 박스 하나 만드는 클래스
    def __init__(self, master, row_idx, col_idx, check_func):
        super().__init__(master)
        self.row_idx = row_idx 
        self.col_idx = col_idx 
        self.check_func = check_func #부모가 준 검사 함수 (중복 체크용)
        
        # 테두리 색상 조정 -> 구분 용이
        self.configure(border_width=1, border_color=DRACULA_COMMENT, fg_color=DRACULA_CURRENT)

        # 상단 프레임 (체크박스, 삭제버튼)
        top_frame = ctk.CTkFrame(self, fg_color="transparent", height=24)
        top_frame.grid(row=0, column=0, sticky="ew", padx=2, pady=2)
        
        # 활성화 여부 체크박스
        self.active_var = ctk.BooleanVar(value=False)
        self.cb = ctk.CTkCheckBox(top_frame, text="On", variable=self.active_var, 
                                  width=40, height=20, font=("Arial", 11, "bold"),
                                  command=self.click_check,
                                  fg_color=DRACULA_PURPLE, hover_color=DRACULA_PINK) #체크박스 색상
        self.cb.pack(side="left", padx=2)

        # X 버튼 (박스 내 모든 내용 지우기)
        self.del_btn = ctk.CTkButton(top_frame, text="x", width=20, height=20, 
                                     fg_color=DRACULA_RED, hover_color="#ff6e6e",
                                     font=("Arial", 10, "bold"),
                                     command=self.clear_data)
        self.del_btn.pack(side="right", padx=2)

        # 과목명 입력창 (다크 테마 적용) , 추후 학교별 강의 정보 자동 연결 시스템으로 발전할 예정
        self.name_entry = ctk.CTkEntry(self, placeholder_text="강의명", height=24, font=("Arial", 11), fg_color=DRACULA_BG, border_color=DRACULA_COMMENT)
        self.name_entry.grid(row=1, column=0, padx=2, pady=1, sticky="ew")

        # 학점 입력창(0보다 큰 정수만)
        self.credit_entry = ctk.CTkEntry(self, placeholder_text="학점", width=50, height=24, fg_color=DRACULA_BG, border_color=DRACULA_COMMENT)
        self.credit_entry.grid(row=2, column=0, padx=2, pady=1, sticky="w")

        # 시간 선택 콤보박스들(요일, 시, 분)
        time_frame = ctk.CTkFrame(self, fg_color="transparent")
        time_frame.grid(row=3, column=0, sticky="w", padx=2)
        
        days = ["월", "화", "수", "목", "금"]
        hours = [f"{h}" for h in range(9, 23)] # 9시 ~ 22시
        mins = [f"{m:02d}" for m in range(0, 60, 10)] #10분 단위
        
        # 콤보박스 스타일 통일 (kwargs 활용)
        cb_kwargs = {"fg_color": DRACULA_BG, "button_color": DRACULA_COMMENT, "border_color": DRACULA_COMMENT}

        self.day_var = ctk.StringVar(value="월")
        ctk.CTkComboBox(time_frame, values=days, variable=self.day_var, width=45, height=22, **cb_kwargs).pack(side="left", padx=1)
        
        # 시작 시간
        self.s_h_var = ctk.StringVar(value="9"); self.s_m_var = ctk.StringVar(value="00")
        ctk.CTkComboBox(time_frame, values=hours, variable=self.s_h_var, width=45, height=22, **cb_kwargs).pack(side="left")
        ctk.CTkLabel(time_frame, text=":").pack(side="left")
        ctk.CTkComboBox(time_frame, values=mins, variable=self.s_m_var, width=45, height=22, **cb_kwargs).pack(side="left")

        ctk.CTkLabel(time_frame, text="~").pack(side="left", padx=2)

        # 종료 시간
        self.e_h_var = ctk.StringVar(value="10"); self.e_m_var = ctk.StringVar(value="00")
        ctk.CTkComboBox(time_frame, values=hours, variable=self.e_h_var, width=45, height=22, **cb_kwargs).pack(side="left")
        ctk.CTkLabel(time_frame, text=":").pack(side="left")
        ctk.CTkComboBox(time_frame, values=mins, variable=self.e_m_var, width=45, height=22, **cb_kwargs).pack(side="left")

        # 메타 정보 (대면/온라인, 강의동)
        meta_frame = ctk.CTkFrame(self, fg_color="transparent")
        meta_frame.grid(row=4, column=0, sticky="w", padx=2)
        
        self.mode_var = ctk.StringVar(value="대면")
        ctk.CTkComboBox(meta_frame, values=["대면","온라인"], variable=self.mode_var, 
                        command=self.change_mode, width=60, height=22, **cb_kwargs).pack(side="left", padx=1)
        
        self.bldg_var = ctk.StringVar(value="")
        self.bldg_cb = ctk.CTkComboBox(meta_frame, values=[], variable=self.bldg_var, width=120, height=22, **cb_kwargs)
        self.bldg_cb.pack(side="left", padx=1)
        
        self.input_widgets = [self.name_entry, self.credit_entry]

    # 체크박스 클릭 시 상위 로직 확인 (평가모드일 때 중복 체크 방지)
    def click_check(self):
        if self.active_var.get():
            if not self.check_func(self.row_idx, self.col_idx):
                self.active_var.set(False) 

    # 모드 변경 시 강의동 콤보박스 활성/비활성 처리 (온라인 수업: 강의동 필요X 때문)

    def change_mode(self, choice):
        if choice == "온라인":
            self.bldg_var.set("")
            self.bldg_cb.configure(state="disabled")
        else:
            self.bldg_cb.configure(state="normal")
            vals = self.bldg_cb.cget("values")
            if vals: self.bldg_var.set(vals[0])

    # 셀 내용 초기화 (X 버튼 누르면 실행), 하나하나 지우려면 불편하기 떄문 (편의성 증가)
    def clear_data(self):
        self.active_var.set(False)
        self.name_entry.delete(0, "end")
        self.credit_entry.delete(0, "end")
        self.day_var.set("월")
        self.s_h_var.set("9"); self.s_m_var.set("00")
        self.e_h_var.set("10"); self.e_m_var.set("00")
        self.mode_var.set("대면")
        self.change_mode("대면")

    # 학교 바뀔 때 강의동 목록 업데이트
    def update_buildings(self, b_list):
        self.bldg_cb.configure(values=b_list)
        if self.mode_var.get() == "대면":
            if b_list:
                # 기존에 선택된 게 목록에 없으면 첫 번째 걸로 바꿈
                if self.bldg_var.get() not in b_list:
                    self.bldg_cb.set(b_list[0])
            else:
                self.bldg_cb.set("")
        else:
            self.bldg_cb.set("")

    # 현재 셀의 입력 데이터 -> 딕셔너리 반환 (저장용)
    def get_data(self):
        return {
            "active": self.active_var.get(), "subject": self.name_entry.get(), "credit": self.credit_entry.get(),
            "day": self.day_var.get(), "s_h": self.s_h_var.get(), "s_m": self.s_m_var.get(),
            "e_h": self.e_h_var.get(), "e_m": self.e_m_var.get(), "mode": self.mode_var.get(), "structure": self.bldg_cb.get()
        }

    #  데이터 로드 시 셀 채우기 (불러오기용)
    def set_data(self, data):
        self.active_var.set(data.get("active", False))
        self.name_entry.delete(0, "end"); self.name_entry.insert(0, data.get("subject", ""))
        self.credit_entry.delete(0, "end"); self.credit_entry.insert(0, data.get("credit", ""))
        self.day_var.set(data.get("day", "월"))
        self.s_h_var.set(data.get("s_h", "9")); self.s_m_var.set(data.get("s_m", "00"))
        self.e_h_var.set(data.get("e_h", "10")); self.e_m_var.set(data.get("e_m", "00"))
        self.mode_var.set(data.get("mode", "대면"))
        self.bldg_cb.set(data.get("structure", ""))
        self.change_mode(self.mode_var.get())

    # 실행 전에 데이터 올바른지 검사 (빈칸이나 숫자 아닌 것 걸러냄) , 불러올 땐 누락 있어도 불러옴 && 실행할 때 검사
    def check_data_valid(self):
        if not self.active_var.get(): return None
        
        subj = self.name_entry.get().strip()
        c_txt = self.credit_entry.get().strip()

        if not subj: raise ValueError(f"{self.row_idx+1}행 {self.col_idx+1}열: [과목명] 누락")
        if not c_txt: raise ValueError(f"{self.row_idx+1}행 {self.col_idx+1}열: [학점] 누락")
        if not c_txt.isdigit() or int(c_txt) <= 0: raise ValueError(f"{self.row_idx+1}행: 학점은 자연수여야 함")
        
        credit = int(c_txt)
        start = int(self.s_h_var.get()) * 60 + int(self.s_m_var.get())
        end = int(self.e_h_var.get()) * 60 + int(self.e_m_var.get())
        
        if end <= start: raise ValueError(f"{self.row_idx+1}행: 종료 시간이 시작보다 빠름") # 시작시간이 종료시간보다 빠르면 안됨

        # 오타 방지를 위해 시간 길이와 학점이 맞는지 확인 (경기대는 10분씩 덜 하기때문. 추후 학교별 정확한 판별법 도입 예정)
        duration_min = end - start
        expected_min_std = credit * 60 
        expected_min_univ = (credit * 60) - 10 
        
        if not (abs(duration_min - expected_min_std) < 5 or abs(duration_min - expected_min_univ) < 5):
            raise ValueError(f"{self.row_idx+1}행 [시간 경고]: 학점({credit})과 시간({duration_min}분) 불일치")

        return {
            "subject": subj, "credit": credit, "day": self.day_var.get(),
            "start_time": f"{self.s_h_var.get()}:{self.s_m_var.get()}",
            "end_time": f"{self.e_h_var.get()}:{self.e_m_var.get()}",
            "mode": self.mode_var.get(), "structure": self.bldg_cb.get()
        }


#자식 클래스: 강의 목록 관리 테이블
# BaseScrollableFrame 상속받음 -> 스크롤 기능 사용
class LectureTable(BaseScrollableFrame): 
    def __init__(self, master, initial_rows=6, max_rows=10, cols=4):
        # 부모 초기화 -> 스크롤 기능 획득
        super().__init__(master) 
        
        self.cols = cols #4열
        self.max_rows = max_rows #최대 늘어날 행 개수 (10개)
        self.initial_rows = initial_rows # 기본 행 개수 기억(6행) -> 사용자 2행만 입력 && 저장 후 불러왔을 때 2행만 로드되는거 방지
        self.is_eval = False #지금 평가모드인지 (False)
        self.buildings = [] 
        
        self.row_frames = [] # 만들어진 행들 담을 리스트
        self.cells_data = [] # 각 칸의 데이터 담을 리스트

        # 처음에 빈 행들 추가
        for _ in range(initial_rows): self.add_new_row()
        
        # 행 추가 버튼 (스크롤 컨텐츠 내부에 배치)
        self.add_btn = ctk.CTkButton(self.scroll_content, text="+ 과목 슬롯 추가", command=self.add_new_row, 
                                     fg_color=DRACULA_GREEN, text_color=DRACULA_BG, hover_color="#69ff94")
        self.add_btn.pack(pady=5, anchor="w", padx=5)
        
        # 버튼에도 스크롤 기능 연결 (부모 메서드 호출) -> 버튼 위에서 스크롤 하면 스크롤 안되는 것 해결하기 위함
        self.connect_wheel(self.add_btn)

    # 기능: 새로운 과목 행 추가하기
    def add_new_row(self):
        if len(self.row_frames) >= self.max_rows: return

        # 버튼을 잠시 숨기고 새 행을 그 위에 추가한 뒤 다시 버튼을 보여줌
        if hasattr(self, 'add_btn') and self.add_btn.winfo_exists():
            self.add_btn.pack_forget()

        row_frame = ctk.CTkFrame(self.scroll_content, fg_color="transparent")
        row_frame.pack(fill="x", pady=2, anchor="w")
        
        # 헤더 (과목1, 과목2...)
        header_frame = ctk.CTkFrame(row_frame, width=60, fg_color="transparent")
        header_frame.pack(side="left", padx=2, fill="y")
        
        idx = len(self.row_frames) + 1
        ctk.CTkLabel(header_frame, text=f"과목{idx}", font=("Arial", 12, "bold"), text_color=DRACULA_FG).pack(pady=(5, 0))
        
        # 삭제 버튼
        del_btn = ctk.CTkButton(header_frame, text="삭제", width=50, height=20, 
                                fg_color=DRACULA_RED, hover_color="#ff6e6e",
                                command=lambda f=row_frame: self.delete_row(f))
        if idx >= 7: del_btn.pack(pady=2) #사용자가 6행 이하로 삭제하는 것 방지
        else: ctk.CTkLabel(header_frame, text="").pack()

        # 셀 생성 반복
        current_cells = []
        for c in range(self.cols):
            cell = LectureCell(row_frame, len(self.row_frames), c+1, self.check_rule)
            cell.pack(side="left", padx=2, fill="y")
            cell.update_buildings(self.buildings)
            current_cells.append(cell)
        
        self.row_frames.append(row_frame)
        self.cells_data.append(current_cells)
        
        # 버튼 다시 하단에 배치
        if hasattr(self, 'add_btn') and self.add_btn.winfo_exists():
            self.add_btn.configure(state="normal", text="+ 과목 슬롯 추가")
            self.add_btn.pack(pady=5, anchor="w", padx=5)
            self.connect_wheel(self.add_btn)

        if len(self.row_frames) >= self.max_rows: 
             self.add_btn.configure(state="disabled", text="최대 10개 도달")
        
        # 새로 생긴 위젯들 -> 스크롤 기능 붙임 && 화면 갱신
        self.connect_wheel(row_frame)
        self.resize_content(None)

    # 기능: 특정 행 삭제
    def delete_row(self, frame):
        try: idx = self.row_frames.index(frame)
        except: return
        frame.destroy()
        self.row_frames.pop(idx)
        self.cells_data.pop(idx)
        
        # 인덱스 라벨 재정렬 (중간 거 지웠을 때 번호 꼬임 방지)
        for i, fr in enumerate(self.row_frames):
            header = fr.winfo_children()[0]
            lbl = header.winfo_children()[0]
            lbl.configure(text=f"과목{i+1}")
            for cell in self.cells_data[i]: cell.row_idx = i
            
        self.add_btn.configure(state="normal", text="+ 과목 슬롯 추가")
        self.resize_content(None)

    # 평가모드 규칙 확인 (한 행에 1개만 선택)
    def check_rule(self, r, c):
        if self.is_eval:
            row = self.cells_data[r]
            for cell in row:
                if cell != row[c-1] and cell.active_var.get():
                    messagebox.showwarning("제한", "평가모드: 한 행에 1개만 선택 가능")
                    return False
        return True
    
    def reset_selection(self):
        for row in self.cells_data:
            for cell in row:
                cell.active_var.set(False)

    # 과목명 중복 체크 (같은 과목 두 번 넣는 거 방지) -> 경기대학교는 연강이 X 따라서 이 로직 선택 -> 추후 학교별 연강 시스템 도입 예정
    def check_duplicate(self):
        seen = {} 
        for r_idx, row in enumerate(self.cells_data):
            for cell in row:
                if cell.active_var.get():
                    name = cell.name_entry.get().strip()
                    if not name: continue
                    # 이름은 같은데 행 번호가 다르면 중복
                    if name in seen and seen[name] != r_idx:
                        return False, f"중복 오류: '{name}'"
                    seen[name] = r_idx
        return True, ""

    # 1열(메인 과목) 학점 합계 체크
    def check_total_credit(self, max_credit):
        total = 0
        for i, row in enumerate(self.cells_data):
            first_cell = row[0]
            if first_cell.active_var.get():
                try:
                    c = int(first_cell.credit_entry.get().strip())
                    total += c
                except: pass
        
        if total > max_credit: return False, f"학점 초과: {total} / {max_credit}"
        return True, ""

    # 활성화된 모든 데이터 수집 && 리스트로 반환
    def get_active_data(self):
        data = []
        for row in self.cells_data:
            group = []
            for cell in row:
                d = cell.check_data_valid() 
                if d: group.append(d)
            if group: data.append(group)
        return data

    def update_buildings(self, b_list):
        self.buildings = b_list
        for row in self.cells_data:
            for cell in row: cell.update_buildings(b_list)

    # 저장용 데이터 내보내기
    def get_save_data(self):
        state = []
        for row in self.cells_data:
            state.append([c.get_data() for c in row])
        return state

    # 기능: 저장된 상태를 불러와서 UI에 반영
    def load_save_data(self, state_data):
        # 목표 행 개수 설정 (저장된 게 많으면 늘리고, 적어도 기본 개수는 유지) 로드했을 때 잔상 데이터가 남는 버그 방지
        target_rows = max(len(state_data), self.initial_rows)

        # 줄 개수 맞추기 (부족하면 추가, 넘치면 삭제)
        while len(self.row_frames) > target_rows:
            self.delete_row(self.row_frames[-1])
        while len(self.row_frames) < target_rows:
            self.add_new_row()

        # 데이터 채워넣기
        for r in range(len(self.row_frames)):
            # 저장된 데이터가 있는 행인지 확인
            row_data = state_data[r] if r < len(state_data) else []

            for c in range(self.cols):
                cell = self.cells_data[r][c]
                if c < len(row_data):
                    # 데이터 있으면 채움
                    cell.set_data(row_data[c])
                else:
                    # 없으면 삭제 (잔상 방지)
                    cell.clear_data()