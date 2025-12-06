import itertools
from models import LectureObj

# 시간표 조합하고 점수 매기는 파일
class ScheduleCalculator:
    def __init__(self, school_info, max_credit, evaluation_mode, priorities, lectures_data):
        # 필요한 기본 정보들 저장
        self.school_info = school_info
        self.max_credit = max_credit
        self.evaluation_mode = evaluation_mode
        self.priorities = priorities
        
        # 입력받은 강의 정보(딕셔너리)를 만든 객체로 변환 -> 리스트에 담음
        #변환 이유: 정보 다루기 쉽게 하기 위함
        self.candidate_groups = [
            [LectureObj(d) for d in row_data] 
            for row_data in lectures_data if row_data
        ]

    # 계산 시작 함수 (외부에서 이 함수를 부름 -> 연산 시작)
    def run_calculation(self):
        result = {"schedule": [], "feedback": [], "score": 0}

        if self.evaluation_mode:
            # 평가 모드: 한 행당 하나의 강의 선택 -> 첫 번째 것만 가져와서 검사
            flat_schedule = [group[0] for group in self.candidate_groups if group]
            is_valid, feedback = self.check_schedule_valid(flat_schedule)
            result['schedule'] = flat_schedule
            result['feedback'] = feedback
        else:
            # 추천 모드: 모든 조합 생성 && 제일 좋은 케이스 찾기
            best_schedule, best_score, logs = self.find_best_schedule()
            if best_schedule:
                # 제일 좋은 시간표 찾음 -> 이동 시간이 얼마나 걸리는지 등 상세 정보를 다시 확인
                _, detailed_feedback = self.check_schedule_valid(best_schedule)
                
                # 결과 창에 보여줄 메시지 정리 (중복되는 내용은 제외)
                final_feedback = [f"[성공] 최적 시간표 도출 (점수: {best_score:.1f})"] + \
                                 [fb for fb in detailed_feedback if "학점" not in fb and "선택하신" not in fb] + \
                                 logs
                
                result['schedule'] = best_schedule
                result['feedback'] = final_feedback
                result['score'] = best_score
            else:
                # 가능한 조합이 하나도 없을 때: 실패 메시지 띄움
                result['feedback'] = ["[실패] 가능한 시간표가 없습니다."] + logs 
        return result

    # 시간표에 문제 없는지 확인(시간 겹침, 학점 초과, 이동 가능 여부..)
    def check_schedule_valid(self, schedule):
        feedbacks = []
        is_valid = True

        # 학점 계산해서 제한 넘는지 확인
        total = sum(l.credit for l in schedule)
        if total > self.max_credit:
            feedbacks.append(f"[학점 초과] {total} > {self.max_credit}") #학점 초과 여부 판단
            if not self.evaluation_mode: is_valid = False
        else:
            feedbacks.append(f"[학점] 총 {total}학점")

        # 요일별로 수업 정리 (비교하기 쉽게 딕셔너리로 생성)
        schedule_by_day = {}
        for l in schedule:
            schedule_by_day.setdefault(l.day, []).append(l)

        # 각 요일마다 수업 시간 충돌 & 이동 시간 체크
        for day, lecs in schedule_by_day.items():
            lecs.sort(key=lambda x: x.start_time) # 시간 순서대로 정렬해야 앞뒤 비교 가능
            
            for i in range(len(lecs)-1):
                curr, next_lec = lecs[i], lecs[i+1]
                
                # 수업시간 충돌 여부 (앞 수업 끝나는 시간이 뒷 수업 시작보다 늦으면 겹침)
                if curr.end_time > next_lec.start_time:
                    feedbacks.append(f"[충돌] {day}요일: '{curr.subject}' <-> '{next_lec.subject}'")
                    if not self.evaluation_mode: is_valid = False
                
                # 이동 시간 체크 (둘 다 대면 수업일 때만/ 온라인 수업 제외)
                elif not curr.check_online() and not next_lec.check_online():
                    gap = next_lec.start_time - curr.end_time #공강 시간 (쉬는 시간)
                    travel = self.school_info.get_move_time(curr.structure, next_lec.structure) #강의동 사이 거리 불러오기
                    margin = gap - travel # 실제 여유 시간
                    
                    # 건물 이름이 길어서 '강의동' 글자 제거
                    s_from = curr.structure.replace("강의동", "")
                    s_to = next_lec.structure.replace("강의동", "")
                    msg = f"[{s_from}->{s_to}] 이동 {travel}분 / 공강 {gap}분"
                    
                    # 여유 시간에 따라 상태 판단
                    # 0분 미만: 이동 불가, 1분 이하: 빠듯함, 나머지: 여유
                    if margin < 0:
                        feedbacks.append(f"[이동불가] {day}요일 {msg} (시간부족)")
                        if not self.evaluation_mode: is_valid = False
                    elif margin <= 1:
                        feedbacks.append(f"[주의] {day}요일 {msg} (빠듯함)")
                    else:
                        feedbacks.append(f"[이동가능] {day}요일 {msg} (여유 {margin}분)")
        
        # 평가 모드: 최종 결과 메시지 추가
        if is_valid and self.evaluation_mode:
             # 충돌이나 이동불가 메시지가 하나도 없으면 성공
             status_msg = "[검증 완료] 실행 가능" if not any("[충돌]" in f or "[이동불가]" in f for f in feedbacks) else "[검증 실패] 문제 발견"
             feedbacks.insert(0, status_msg)

        return is_valid, feedbacks

    # 모든 경우의 수 고려 -> 제일 좋은 케이스 선택
    def find_best_schedule(self):
        # itertools.product 함수를 사용 -> 가능한 모든 조합을 한 번에 생성
        all_cases = itertools.product(*self.candidate_groups)
        best_schedule = None
        best_score = -999999 # 기본 점수는 아주 낮게 설정해서 나중에 갱신되게 함
        logs = []
        valid_cnt = 0
        excluded_by_credit = 0
        
        for case in all_cases:
            schedule = list(case)
            
            # 학점 넘으면 계산할 필요도 없이 패스(최적화)
            if sum(l.credit for l in schedule) > self.max_credit:
                excluded_by_credit += 1
                continue

            # 유효한 시간표인지 확인하고 점수 계산
            is_valid, _ = self.check_schedule_valid(schedule)
            if is_valid:
                valid_cnt += 1
                score = self.get_score(schedule)
                
                # 지금까지 찾은 것 중 점수가 제일 높으면 저장
                if score > best_score:
                    best_score = score
                    best_schedule = schedule
        
        logs.append(f"검토 조합: 총 {valid_cnt}개") # 검토한 모든 경우의 수
        if excluded_by_credit > 0: logs.append(f"(학점 초과 제외: {excluded_by_credit}개)") # 제외된 조합 수 표시
            
        return best_schedule, best_score, logs

    # 점수 계산기 (가중치 알고리즘 적용)
    def get_score(self, schedule):
        score = 0
        weights = [100, 50, 20] # 1순위는 100점, 2순위는 50점... 이런 식으로 가중치 설정
        
        # 중복된 우선순위는 제거하고 순서대로 정리
        unique_priorities = []
        [unique_priorities.append(p) for p in self.priorities if p != "선택 안함" and p not in unique_priorities]

        if not schedule: return -9999

        for idx, p in enumerate(unique_priorities):
            if idx >= 3: break # 우선순위 3개까지만 계산
            w = weights[idx]
            
            if "공강 확보" in p:
                # 온라인 수업은 학교 안 가니까 공강으로 설정
                offline_days = {l.day for l in schedule if not l.check_online()}
                num_days = len(offline_days)
                # 학교 안 가는 날이 많을수록 점수 부여 (하루당 가중치 * 2)
                score += ((5 - num_days) * w * 2)
                # 주 5일 다 가면 감점
                if num_days == 5: score -= (w * 0.5)

            elif "매일 등교" in p:
                # 공강 확보 반대 개념
                offline_days = {l.day for l in schedule if not l.check_online()}
                num_days = len(offline_days)
                score += (num_days * w * 2) # 학교 가는 날 -> 점수 증가
                if num_days <= 2: score -= (w * 0.5) # 2일 이하 -> 감점

            elif "오후수업 선호" in p:
                # 12시(720분) 이후 시작하는 수업 개수 세기
                pm_cnt = sum(1 for l in schedule if l.start_time >= 720) 
                am_cnt = len(schedule) - pm_cnt
                if schedule: score += (pm_cnt / len(schedule)) * w * 3 # 12시 이후 수업 비율만큼 점수 증가
                score -= am_cnt * (w * 0.4) # 12시 이전 수업 -> 감점

            elif "오전수업 선호" in p:
                am_cnt = sum(1 for l in schedule if l.start_time < 720) 
                pm_cnt = len(schedule) - am_cnt
                if schedule: score += (am_cnt / len(schedule)) * w * 3 # 12시 이전 수업 -> 점수 증가
                score -= pm_cnt * (w * 0.4) # 12시 이후 수업 -> 감점

            elif "주요과목 집중" in p:
                # 3학점 이상인 과목(주요과목)이 많으면 점수 부여
                major_cnt = sum(1 for l in schedule if l.credit >= 3) # 3학점 이상, 주요과목 -> 점수 증가
                score += major_cnt * (w * 0.5)

            elif "이동 거리 최소화" in p:
                total_move = 0
                sorted_sched = sorted(schedule, key=lambda x: (x.day, x.start_time))
                for i in range(len(sorted_sched)-1):
                    curr, next_l = sorted_sched[i], sorted_sched[i+1]
                    # 같은 날 대면 수업끼리만 거리 계산/온라인 제외
                    if curr.day == next_l.day and not curr.check_online() and not next_l.check_online():
                         total_move += self.school_info.get_move_time(curr.structure, next_l.structure)
                penalty = 5 if idx == 0 else (3 if idx == 1 else 1) # 우선순위 높을수록 이동거리에 대한 패널티 강하게 부여
                score -= (total_move * penalty)

        return score