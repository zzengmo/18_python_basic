import random

# 1~9 사이의 서로 다른 4자리 숫자 생성
numbers = list(range(1, 10))
computer = random.sample(numbers, 4)

print("숫자야구 게임을 시작합니다! (1~9 사이의 중복 없는 4자리 숫자)")

attempts = 0

while True:
  user_input = input("4자리 숫자를 입력하세요 (예: 1234): ")

  # 입력값 검증 (4자리 숫자인지, 중복 없는지 확인)
  if not user_input.isdigit() or len(user_input) != 4:
    print("잘못된 입력입니다. 1~9 사이의 중복 없는 4자리 숫자를 입력해주세요.")
    continue

  user = [int(x) for x in user_input]

  if len(set(user)) != 4:
    print("중복된 숫자가 없어야 합니다.")
    continue

  attempts += 1
  strike = 0
  ball = 0

  # 스트라이크 및 볼 판정
  for i in range(4):
    if user[i] == computer[i]:
      strike += 1
    elif user[i] in computer:
      ball += 1

  # 결과 출력
  if strike == 4:
    print(f"정답입니다! {attempts} 번 만에 맞추셨습니다.")
    break

  if strike == 0 and ball == 0:
    print("아웃!")
  else:
    print(f"{strike} 스트라이크, {ball} 볼")