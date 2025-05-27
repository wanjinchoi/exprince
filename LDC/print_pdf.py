import os
import subprocess

def main(checklist):
    # 프린트할 PDF 파일들이 있는 폴더 경로를 지정하세요
    folder_path = 'C:\\ArgosRPA\\print\\20240928'

    # 폴더 내의 모든 PDF 파일을 가져옵니다
    pdf_files = [f for f in os.listdir(folder_path) if
                 f.lower().endswith('.pdf')]

    # SumatraPDF의 실행 파일 경로 (시스템에 맞게 수정 필요)
    sumatra_path = r'C:\Program Files\SumatraPDF\SumatraPDF.exe'

    for pdf_file in pdf_files:
        full_path = os.path.join(folder_path, pdf_file)
        try:
            # SumatraPDF를 사용하여 파일 인쇄
            subprocess.run([sumatra_path, '-print-to-default', full_path],
                           check=True)
            print(f"'{pdf_file}' 파일을 성공적으로 프린트했습니다.")
        except Exception as e:
            print(f"'{pdf_file}' 파일을 프린트하는 중 에러 발생: {e}")
if __name__ == "__main__":
    main('000015100227')

