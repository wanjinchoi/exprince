import os
from datetime import datetime, timedelta
import imageio
import openpyxl as op
import glob
import imageio.v2
import shutil
from openpyxl.styles import Alignment
import yaml

def main(checklist):
    current_date_str = datetime.now().strftime("%Y-%m-%d")
    current_date = datetime.strptime(current_date_str, "%Y-%m-%d")
    yesterday_date = datetime.now() - timedelta(days=1)
    yesterday_date_str = yesterday_date.strftime("%Y-%m-%d")

    one_week_ago = datetime.now() - timedelta(days=7)
    one_week_ago_str = one_week_ago.strftime("%Y-%m-%d")

    with open('road.yaml', 'r') as file:
        data = yaml.safe_load(file)
        report_path = os.path.normpath(data['report_path'])
        all_image_path = os.path.normpath(data['all_image_path'])
        gifolder_path = os.path.normpath(data['gifolder_path'])


    result_folder_path = report_path + current_date_str+'\\'
    image_folder_path = all_image_path+ current_date_str+'\\'
    one_week_agof_path = all_image_path + one_week_ago_str + '\\'
    store_xlsx_path = result_folder_path + current_date_str + '_ARGOS C-CUBE Report_v1.0.xlsx'
    git_folder_path = gifolder_path + current_date_str
    y_gif_folder_path= gifolder_path + yesterday_date_str

    wb = op.load_workbook(store_xlsx_path)
    ws = wb['Report']

    ##오늘자 폴더 없으면 만들기

    if not os.path.exists(git_folder_path):
        os.mkdir(git_folder_path)

    ## 일주일지난 폴더 삭제
    if os.path.exists(one_week_agof_path):
        shutil.rmtree(one_week_agof_path)
        print(f"{one_week_agof_path} and its contents have been deleted.")

    flist = sorted(glob.glob(image_folder_path + '\\' + '*.png'),key=os.path.getmtime)

    r_i = max((a.row for a in ws['B'] if a.value is not None))
    start_i= max((a.row for a in ws['J'] if a.value is not None))

    #GIF파일과 리포트의 시간 및 캠번호일 매칭시키기 위해 리포트 내용 가져오기
    for i in range(start_i+1, r_i+1):
        detect_time = ws['C'+str(i)].value
        detect_time_split = detect_time.split('\n')
        r_detect_time = detect_time_split[1]
        screen= ws["D"+str(i)].value
        cam_name = ws["F" + str(i)].value

        #시간 전환
        detect_time_t =  datetime.strptime(r_detect_time, '%H:%M:%S')
        filtered_files = []

        #5분미만 나는 것들을 filtered_files = []에 담기
        for file_path in flist:
            # 파일 경로에서 파일 이름만 추출
            file_name = file_path.split('\\')[-1]
            # 파일 이름을 '_' 기준으로 분할하여 필요한 요소 추출
            file_elements = file_name.split('_')
            time_str = file_elements[0]  # 시간 부분 추출
            screen_str = file_elements[1]  # PC 이름 부분 추출
            cam_str = file_elements[2]  # 카메라 번호 부분 추출
            file_time = datetime.strptime(time_str, '%H%M%S')

            # PC 이름과 카메라 번호가 주어진 값과 일치하고 시간 차이가 2분 미만인 경우 리스트에 추가
            if screen_str == screen and cam_str == cam_name:
                time_difference = abs((file_time - detect_time_t).total_seconds()) / 60
                if time_difference < 2 and file_time >= detect_time_t:
                    filtered_files.append(file_path)
            # 담은 것들을 gif파일 담아 삽입하기

        if len(filtered_files) > 0:
            # if i == 32 or i == 8:
            #r     print(f"make : {i}번째 {filtered_files}")
            x = r_detect_time.split(':')
            new_name = x[0] + '_' + x[1] + '_' + x[2] + '_' + screen + '_' + cam_name + '.gif'
            gif_file = os.path.join(git_folder_path, new_name)

            #이미 만들어진거랑 삽입된거는 pass
            git_file_list = sorted(glob.glob(git_folder_path + '\\' + '*.gif'),key=os.path.getmtime)
            y_gif_file_list = sorted(glob.glob(y_gif_folder_path + '\\' + '*.gif'),key=os.path.getmtime)
            if os.path.join(git_folder_path,new_name) in git_file_list or os.path.join(y_gif_folder_path, new_name) in y_gif_file_list:
                continue

            with imageio.get_writer(gif_file, mode='I', duration=400,loop=0) as writer:
                for file_path in filtered_files:
                    image = imageio.v2.imread(file_path)
                    writer.append_data(image)

            # 가운데 정렬
            center_aligned = Alignment(horizontal='center',vertical='center')
            # gif파일 이름을 하이퍼링크로 넣기
            ws.cell(row=i, column=10).hyperlink = gif_file
            ws.cell(row=i, column=10).value = gif_file.split('\\')[-1]
            ws.cell(row=i, column=10).style = "Hyperlink"
            ws.cell(row=i, column=10).alignment = center_aligned

            # GIF 파일에 사용된 이미지 삭제
            for file_path in filtered_files:
                if os.path.exists(file_path):
                    os.remove(file_path)

    wb.save(store_xlsx_path)
    wb.close()

    # #### all_image_folder내 이미지 삭제
    # png_files = glob.glob(os.path.join(image_folder_path, '*.png'))
    #
    # # 각 파일을 반복하면서 삭제
    # for file_path in png_files:
    #     os.remove(file_path)

    # #프레임수를 줄임
    # for idx, file_path in enumerate(filtered_files[::2]):
    #     image = imageio.v2.imread(file_path)
    #     image_pil = Image.fromarray(image)
    #     # Resize image
    #     resized_image = image_pil.resize((width_px, height_px))
    #     image_np = np.array(resized_image)
    #     writer.append_data(image_np)
    # print(f"GIF file '{gif_file}' has been created.")


    # ## 엑셀에 gif파일 삽입버전1
    # app = xw.App(visible=False)
    # workbook = xw.Book(store_xlsx_path)
    # sheet = workbook.sheets['Report']
    #
    # sheet.pictures.add(gif_file,left=sheet.range('L' + str(i)).left,top=sheet.range('L' + str(i)).top)
    ##gif 파일 삽입 버전2
    ## 가운데맞춤 옵션




if __name__ == "__main__":
    main('aa')
