from Arcapi import AsyncApi
import discord
from discord.ext import commands
import asyncio
import pickle
import websockets
import random
import os

info_list = [{} for i in range(0)]
recent_po_list = [{} for k in range(0)]
user_code = "552925754"

# {'user_id': , 'song_id': , 'difficulty': , 'score': , 'shiny_perfect_count': , 'perfect_count': , 'near_count': , 'miss_count': , 'health': , 'modifier': , 'time_played': , 'best_clear_type': , 'clear_type': , 'name': , 'character': , 'is_skill_sealed': , 'is_char_uncapped': , 'rank': , 'constant': , 'rating': , 'song_date': }
api_ = [{}]
sub_api_ = [{}]

client = commands.Bot(command_prefix=':A ')


# 난이도 출력 함수
def showDif(dif):
    if dif == 0:
        return "PST"
    elif dif == 1:
        return "PRS"
    elif dif == 2:
        return "FTR"
    elif dif == 3:
        return "BYD"


def showCType(c_type, is_FPM):
    if c_type is None or is_FPM is None:
        return " "
    elif is_FPM:
        return " [FPM]"
    elif c_type == 1:
        return " [NC]"
    elif c_type == 2:
        return " [FC]"
    elif c_type == 3:
        return " [PM]"
    elif c_type == 4:
        return " [EC]"
    elif c_type == 5:
        return " [HC]"


# 이름(not song_id) 출력 함수
def showName(name_text):
    return api_[0].get(name_text).get('en')


# api_에서 유저 정보를 선택해서 가져오는 함수
def get_info(API):
    var = {'name': showName(API.get('song_id')), 'dif': API.get('difficulty'), 'score': API.get('score'),
           'const': API.get('constant'), 'potential': API.get('rating'),
           'note': API.get('perfect_count') + API.get('near_count') + API.get('miss_count'),
           'health': API.get('health'), 'c_type': API.get('best_clear_type'),
           'is_FPM': API.get('shiny_perfect_count') == API.get('note')}  # health는 반갈죽 여부를 위함
    return var


def get_recent(API):
    var = {'name': showName(API.get('song_id')), 'dif': API.get('difficulty'), 'score': API.get('score'),
           'const': API.get('constant'), 'potential': API.get('rating'),
           'note': API.get('perfect_count') + API.get('near_count') + API.get('miss_count'),
           'health': API.get('health'), 'c_type': API.get('clear_type'),
           'is_FPM': API.get('shiny_perfect_count') == API.get('note')}  # health는 반갈죽 여부를 위함
    return var


# 정렬 시스템 함수
def arrange(info_type, base_list):
    type_list = [{} for q in range(min(60, len(base_list)))]

    type_list[0] = base_list[0]
    for i in range(1, len(base_list)):
        if i < 60:
            for j in range(i):
                if base_list[i].get(info_type) > type_list[j].get(info_type):
                    for k in range(i, j, -1):
                        type_list[k] = type_list[k - 1]
                    type_list[j] = base_list[i]
                    break
            else:
                type_list[i] = base_list[i]
        else:
            break

    return type_list


async def get_api_coroutine():
    global api_, sub_api_, user_code, info_list, recent_po_list

    while True:
        # User 파일 불러오기
        try:
            with open("user.bin", "rb") as f:
                user_data = pickle.load(f)

        except FileNotFoundError:  # 파일이 없으면
            with open("user.bin", "wb+") as f:
                user_data = []
                pickle.dump(user_data, f)

        # user_code 가 파일 내에 없는 경우
        if user_code not in user_data:
            user_data.append(user_code)

        # RL 파일 불러오기
        try:
            with open("recent_list.bin", "rb") as f:
                RL_data = pickle.load(f)

        except FileNotFoundError:  # 파일이 없으면
            with open("recent_list.bin", "wb+") as f:
                RL_data = dict()
                pickle.dump(RL_data, f)

        # 등록되어 있는 유저 수만큼 반복
        for i in range(len(user_data)):

            if user_data[i] not in RL_data:
                RL_data[user_data[i]] = [{} for j in range(0)]

            data = AsyncApi(user_data[i])
            try:
                sub_api_ = await data.constants(start=7, end=12)

            # 없는 user code이거나 타이리츠, 히카리를 입력한 경우는 예외 처리
            except websockets.exceptions.ConnectionClosedError:
                user_data.remove(user_code)
                user_code = "552925754"
                break

            if user_data[i] == "000000001" or user_data[i] == "000000002":
                user_data.remove(user_code)
                user_code = "552925754"
                break

            # 현재 불러온 임시 api_가 user_code의 것이라면
            if user_data[i] == user_code:
                info_list = [{} for i in range(0)]

                api_ = sub_api_
                for j in range(2, len(api_)):
                    for info in api_[j]:
                        info_list.append(get_info(info))

            # 최근 곡 하나를 불러옴
            recent_api_ = get_recent(sub_api_[1].get('recent_score')[0])

            if len(RL_data[user_data[i]]) == 0 or recent_api_ != RL_data[user_data[i]][0]:  # 결과가 update된 경우
                if (len(recent_po_list) < 10 or not (
                        recent_api_.get('potential') <= recent_po_list[9].get('potential') and recent_api_.get(
                        'score') >= 9800000)) or recent_api_.get('health') != -1:
                    # Recent Top 10 기록이 아니고, EX 이상인 경우와 반갈죽 당한 경우는 제외

                    for j in range(len(RL_data[user_data[i]]) - 1, -1, -1):  # recent_list를 뒤로 밈.
                        if j == len(RL_data[user_data[i]]) - 1:
                            RL_data[user_data[i]].append(RL_data[user_data[i]][j])
                        else:
                            RL_data[user_data[i]][j + 1] = RL_data[user_data[i]][j]

                    if len(RL_data[user_data[i]]) == 0:
                        RL_data[user_data[i]].append(recent_api_)
                    else:
                        RL_data[user_data[i]][0] = recent_api_

                    with open("recent_list.bin", "wb") as f:  # RL_data 저장
                        pickle.dump(RL_data, f)

            if user_data[i] == user_code:
                recent_po_list = arrange('potential', RL_data[user_code])  # recent_po_list 정렬

        with open("user.bin", "wb") as f:  # user_data 저장
            pickle.dump(user_data, f)

        await asyncio.sleep(153)
        print(recent_po_list)


@client.event
async def on_ready():
    print("Bot ID : " + str(client.user.id))
    print("System Online")
    await client.change_presence(status=discord.Status.online)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(await get_api_coroutine())


@client.command(name="login", pass_context=True)
# No.001 로그인 명령
async def login(ctx, code):
    global user_code
    await ctx.send("login 중입니다.")
    user_code = code
    await asyncio.sleep(10)
    await ctx.channel.purge(limit=1)
    await ctx.send("login이 완료되었습니다.\n[주의] 없는 유저 코드를 입력한 경우에는 자동으로 기본 설정 계정으로 연결됩니다.")


@client.command(name="best", pass_context=True)
# No.002 최고 퍼텐셜 순으로 출력 명령
async def showBest(ctx):
    global info_list

    potential_list = arrange('potential', info_list)

    BF_potential = 0  # 최고 기록 퍼텐셜 합 계산
    for i in range(len(potential_list)):
        if i < 30:
            BF_potential += potential_list[i].get('potential')
    BF_potential /= 30

    embed = discord.Embed(title="퍼텐셜 기록 상위 30개 [User : " + api_[1].get('name') + "]\n" +
                                "(Best Frame Potential : " + "{0:.3f}".format(BF_potential) + ")"
                          , description="--------------------------------------------------", color=0xffff00)
    for i in range(len(potential_list)):
        if i < 45:
            embed.add_field(name=str(i + 1) + ". " + potential_list[i].get('name') + " [" + showDif(
                potential_list[i].get('dif')) + "/" + str(potential_list[i].get('const')) + "]"
                            , value=str(potential_list[i].get('score')) + showCType(potential_list[i].get('c_type'), potential_list[i].get('is_FPM'))
                                    + " (" + "{0:.3f}".format(potential_list[i].get('potential')) + ")", inline=False)

            if i % 15 == 14 or i == len(potential_list) - 1:
                await ctx.send(embed=embed)
                embed = discord.Embed(description="--------------------------------------------------", color=0xffff00)


@client.command(name="recent", pass_context=True)
# No.003 가장 최근 플레이한 곡 출력
async def showPlaytime(ctx):
    global recent_po_list

    rank = 0  # 기록되는 랭크; 조건을 만족할 떄만 update
    i = 0  # recent_po_list의 번호; 반복할 때마다 무조건 update
    print_list = []
    RC_potential = 0
    for i in range(len(recent_po_list)):
        is_repeated = False
        for j in range(i):
            if recent_po_list[i].get('name') == recent_po_list[j].get('name') and recent_po_list[i].get('dif') == recent_po_list[j].get('dif'):
                is_repeated = True
                break

        if not is_repeated:
            print_list.append(recent_po_list[i])
            if rank < 10:
                RC_potential += print_list[rank].get('potential')
            rank += 1
        i += 1

    RC_potential /= 10

    embed = discord.Embed(title="최근 기록 상위 10개 [User : " + api_[1].get('name') + "]\n" +
                                "(Recent Frame Potential : " + "{0:.3f}".format(RC_potential) + ")"
                          , description="[주의] Bot에서의 Recent Frame Potential은 실제값과 다를 수 있습니다.\n" +
                                        "[주의] Bot에 login한 후 20~30번 정도 플레이해야 정확한 결과를 얻을 수 있습니다.\n" +
                                        "--------------------------------------------------", color=0xffff00)
    for i in range(len(print_list)):
        embed.add_field(
            name=str(i + 1) + ". " + print_list[i].get('name') + " [" + showDif(print_list[i].get('dif')) + "/" + str(
                print_list[i].get('const')) + "]"
            , value=str(print_list[i].get('score')) + showCType(print_list[i].get('c_type'), print_list[i].get('is_FPM'))
                    + " (" + "{0:.3f}".format(print_list[i].get('potential')) + ")",
            inline=False)

        if i % 10 == 9 or i == len(print_list) - 1:
            await ctx.send(embed=embed)
            embed = discord.Embed(description="--------------------------------------------------", color=0xffff00)


@client.command(name="recommend", pass_context=True)
# No.004 곡 추천 시스템
async def recommend(ctx):
    global info_list, api_

    p = api_[1].get('rating') / 100

    # 곡 선정
    while True:
        r = random.randint(0, len(info_list))
        random_api_ = info_list[r]

        # 일반적인 경우 / 아닌 경우(곡 보면 상수가 너무 낮은 경우)는 r 다시 뽑기
        if random_api_.get('const') + 2.5 >= p:
            break

    # 목표 퍼텐셜 계산
    const = random_api_.get('const')
    note = random_api_.get('note')
    goal_poten = random_api_.get('potential') + 0.05

    # 목표 점수 계산
    # PM이 목표인 경우
    if goal_poten >= const + 2:
        goal_score = 10000000
    elif goal_poten >= const + 1:
        goal_score = (goal_poten - const - 1) * 200000 + 9800000
    else:
        goal_score = (goal_poten - const) * 300000 + 9500000

    # 목표 far 수 계산
    far = 0
    while True:
        # 목표 점수보다 far 환산 점수가 더 높은 경우
        if (note - far / 2) / note * 10000000 >= goal_score:
            far += 1
        else:
            break
    far -= 1  # 보정값

    embed = discord.Embed(title="곡 추천 [User : " + api_[1].get('name') + "]", color=0xaaaaaa)
    embed.add_field(name=random_api_.get('name') + " [" + showDif(random_api_.get('dif')) + "/" + str(const) + "]"
                    , value=str(int(goal_score)) + " (" + "{0:.3f}".format(min(goal_poten, const + 2)) + ")\n" +
                            "<허용 far 수> " + str(far), inline=False)

    await ctx.send(embed=embed)
    
access_token = os.environ["BOT_TOKEN"]
client.run(access_token)
