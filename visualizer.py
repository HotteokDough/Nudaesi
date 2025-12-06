import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import hashlib
import os
from matplotlib import font_manager, rc

# 시각화 담당: 계산된 시간표 데이터를 받아서 그래프(이미지)로 그려주는 파일 (matplotlib 이용)
class ScheduleVisualizer:
    def __init__(self):
        # 한글 폰트 설정
        self.set_korean_font()

    # 한글 폰트 깨짐 방지 함수
    # 윈도우 != 맥 (폰트 설정 방법) -> try-except로 처리
    def set_korean_font(self):
        try:
            if os.name == 'nt': # 윈도우 운영체제
                font_name = font_manager.FontProperties(fname="c:/Windows/Fonts/malgun.ttf").get_name()
                rc('font', family=font_name)
            else: # 맥 || 리눅스
                rc('font', family='AppleGothic')
            plt.rcParams['axes.unicode_minus'] = False #  마이너스 기호 깨짐 방지
        except: pass

    # 기능: 과목 이름에 따라 항상 똑같은 색상을 정해주는 함수
    # 랜덤: 매번 색이 바뀌어서 헷갈림, 해시(Hash) 사용 -> 색상 고정
    def pick_color(self, subject):
        # 파스텔톤 색상
        colors = ['#FFB3BA', '#FFDFBA', '#FFFFBA', '#BAFFC9', '#BAE1FF', '#E6B3FF', '#FFCCE5', '#D4F0F0', '#E0BBE4', '#957DAD', '#FEC8D8', '#FF9AA2', '#E2F0CB', '#B5EAD7', '#C7CEEA']
        
        # 과목명 글자 -> 숫자 변환(Hash) && 리스트 인덱스로 사용
        hash_val = int(hashlib.md5(subject.encode('utf-8')).hexdigest(), 16)
        return colors[hash_val % len(colors)]

    # 핵심 기능: 시간표 그래프 그리기 (x축: 요일, y축: 시간)
    # Matplotlib 라이브러리를 사용해서 직접 도형 그리기
    def draw_schedule_graph(self, schedule, school_info):
        #  이전에 그려진 그래프가 있다면 삭제(겹침 방지)
        plt.close('all') 
        
        # 그래프와 축 생성 (figsize = 8x8인치)
        fig, ax = plt.subplots(figsize=(8, 8))
        days = ["월", "화", "수", "목", "금"]
        
        # Y축(시간) 범위 자동으로 설정
        # 수업이 아침 9시~오후 6시 사이 -> 수업 있는 부분만 나타냄
        # 야간 수업 있으면 그래프를 더 길게 늘리기
        if schedule:
            # 시간표에 있는 수업 중 가장 빠른 시작 시간과 늦은 종료 시간을 찾기
            min_t = min(l.start_time for l in schedule)
            max_t = max(l.end_time for l in schedule)
            
            # 기본 9시~18시로 하되, 수업 시간에 맞춰서 위아래로 늘림
            start_h = min(9, int(min_t // 60))
            end_h = max(18, int(max_t // 60) + 1)
        else:
            # 시간표가 없으면 기본값 (9시 ~ 18시)
            start_h, end_h = 9, 18
        
        # 분 단위로 변환
        start_min_limit = start_h * 60
        end_min_limit = end_h * 60

        # Y축 설정 (시간표 시간: 내림차순 -> 순서 뒤집기)
        # set_ylim(아래쪽 끝, 위쪽 끝) -> 큰 숫자가 아래 위치
        ax.set_ylim(end_min_limit, start_min_limit)
        
        # 1시간 간격으로 눈금 표시 (9:00, 10:00 등)
        ax.set_yticks([h*60 for h in range(start_h, end_h + 1)])
        ax.set_yticklabels([f"{h}:00" for h in range(start_h, end_h + 1)])
        
        # 30분 단위로 작은 눈금선 표시 (편리성)
        ax.yaxis.set_minor_locator(ticker.MultipleLocator(30))
        
        # 격자 그리기
        ax.grid(axis='y', which='major', linestyle='-', alpha=0.7) # 굵은 선
        ax.grid(axis='y', which='minor', linestyle=':', alpha=0.4) # 얇은 선

        # X축 설정 (월~금, 요일로 설정)
        ax.set_xlim(-0.5, 4.5)
        ax.set_xticks(range(5))
        ax.set_xticklabels(days)
        
        # 데이터 정리: 요일별로 수업을 분류 (공강, 매일가기 등 우선순위에서 고려하기 위함)
        schedule_by_day = {d: [] for d in days}
        for l in schedule:
            if l.day in days: schedule_by_day[l.day].append(l)

        # 요일별로 반복하면서 그리기
        for d_idx, day in enumerate(days):
            lecs = schedule_by_day[day]
            if not lecs: continue # 수업 없으면 다음 요일로 건너뛰기

            # 알고리즘: 스캔라인 기법 사용
            # 하루 1440분을 1분 단위 배열로 만듦 && 각 분마다 수업이 몇 개 있는지 체크 (시간표 충돌 여부 정확하게 판단 가능)
            timeline = [[] for _ in range(1440)]
            for lec in lecs:
                for t in range(lec.start_time, lec.end_time):
                    if 0 <= t < 1440: timeline[t].append(lec)

            # 상태 변수 초기화
            current_state = "empty" # 현재 상태 (빈칸 / 수업1개 / 충돌)
            block_start = 0         # 상태가 시작된 시간
            block_lectures = []     # 그 시간에 있는 수업들

            # 아침 ~ 저녁: 1분씩 검사하면서 스캔
            for t in range(start_min_limit, end_min_limit + 1):
                current_lecs = timeline[t] if t < 1440 else []
                
                # 현재 분의 상태 판단
                if not current_lecs: new_state = "empty"        # 수업 없음
                elif len(current_lecs) == 1: new_state = "single" # 정상 수업
                else: new_state = "conflict"                      # 수업 겹침(충돌)
                
                # 상태 바뀌었는지 확인 (예: 수업 시작, 수업 끝, 수업 바뀜)
                is_changed = (new_state != current_state)
                if new_state == "single" and current_state == "single":
                    # 이전 시간(1분 전)과 같은 수업인지 확인 (다르면 새로운 블록 시작)
                    if current_lecs[0] != block_lectures[0]: is_changed = True
                
                # 상태 바뀌었다면, 방금 전까지의 블록 그림 (한줄한줄씩 그리는건 비효율적 -> 한번에 그리기)
                if is_changed:
                    if current_state != "empty":
                        dur = t - block_start # 지속 시간 (높이)
                        
                        # 시간표 충돌 (빨간 박스)
                        if current_state == "conflict":
                            ax.bar(d_idx, dur, bottom=block_start, color='#ffcccc', edgecolor='red', width=0.8, align='center', alpha=0.9, zorder=10)
                            ax.text(d_idx, block_start + dur/2, "충돌!", ha='center', va='center', fontsize=9, fontweight='bold', color='red', zorder=11)
                        
                        # 정상 수업 (색상 박스)
                        elif current_state == "single":
                            lec = block_lectures[0]
                            
                            # 온라인 수업은 연두색(고정), 대면 수업은 과목별 고유색
                            if lec.check_online():
                                box_color = '#D0F0C0'; bldg_txt = "온라인 수업"
                            else:
                                box_color = self.pick_color(lec.subject)
                                bldg_txt = lec.structure.replace("강의동", "\n강의동") # 줄바꿈

                            # 막대 그래프 그리기 (x: 요일인덱스, height: 수업시간, bottom: 시작시간)
                            ax.bar(d_idx, dur, bottom=block_start, color=box_color, edgecolor='white', width=0.8, align='center', alpha=0.9, zorder=5)
                            
                            # 텍스트 표시를 위한 시간 계산 (몫 && 나머지)
                            sh, sm = divmod(lec.start_time, 60)
                            eh, em = divmod(lec.end_time, 60)
                            time_str = f"{int(sh):02d}:{int(sm):02d}~{int(eh):02d}:{int(em):02d}"
                            
                            # 예외처리: 1학점짜리 수업 글자가 짤림 방지 -> 65분 이하 수업 시간 텍스트 제외 && 크기 줄이기
                            font_sz = 7 if dur <= 65 else 8
                            label_text = f"{lec.subject}\n{bldg_txt}" if dur <= 65 else f"{lec.subject}\n{time_str}\n{bldg_txt}"
                            
                            # 박스 정중앙에 텍스트 배치
                            ax.text(d_idx, lec.start_time + (lec.end_time - lec.start_time)/2, label_text, ha='center', va='center', fontsize=font_sz, fontweight='bold', zorder=6, wrap=True, clip_on=True)

                    # 상태 업데이트 (다음블록 시작)
                    current_state = new_state
                    block_start = t
                    block_lectures = current_lecs

            # 이동 시간 막대 그리기 (수업 && 수업 사이)
            # 시간순으로 수업 정렬 (바로 이전, 이후 수업 간 시간 비교해야 하기때문)
            sorted_lecs = sorted(lecs, key=lambda x: x.start_time)
            for i in range(len(sorted_lecs) - 1):
                curr, next_l = sorted_lecs[i], sorted_lecs[i+1]
                
                # 앞 수업 끝과 뒷 수업 시작하기 전 틈 있다면
                if curr.end_time < next_l.start_time:
                     # 둘 다 대면수업일 때만(온라인 제외) 이동 시간 계산
                     if not curr.check_online() and not next_l.check_online():
                        gap = next_l.start_time - curr.end_time # 공강 시간
                        travel = school_info.get_move_time(curr.structure, next_l.structure) #이동 시간
                        margin = gap - travel # 여유 시간 = 공강 시간 - 이동 시간
                        
                        # 여유 시간에 따라 색깔 다르게 표시
                        bar_color = 'lightgray' # 기본: 회색
                        if margin < 0: bar_color = 'red' # 불가능: 빨강
                        elif margin <= 1: bar_color = 'orange' # 서둘러: 주황
                        
                        # 이동 시간 막대 그리기 (빗금 무늬 추가)
                        ax.bar(d_idx, gap, bottom=curr.end_time, width=0.3, color=bar_color, alpha=0.8, hatch='///', zorder=3)

        # 레이아웃 깔끔하게 정리 -> 반환
        plt.tight_layout()
        return fig