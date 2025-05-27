import pandas as pd
import os
import shutil
import openpyxl
from openpyxl.drawing.image import Image
import re
from PIL import Image
import time

for root, dirs, files in os.walk(r"X:\〔2〕   사 진 대 장"):
    for file in files:
        if file == "Thumbs.db" or file == "desktop.ini":
            print("Thumbs.db, desktop.ini 파일 삭제")
            os.remove(root + "\\" + file)
#####################################################################################################
# 변수 초기화
# 사진 대장 작업 명칭 들어갈 셀 위치 리스트
job_name_top = ['K13', 'U13', 'AE13', 'AO13', 'AY13', 'BI13', 'BS13', 'CC13',
                'CM13', 'CW13', 'DG13', 'DQ13', 'EA13',
                'EK13', 'EU13', 'FE13', 'FO13', 'FY13', 'GI13', 'GS13', 'HC13',
                'HM13', 'HW13', 'IG13', 'IQ13', 'JA13',
                'JK13', 'JU13', 'KE13', 'KO13', 'KY13', 'LI13', 'LS13', 'MC13',
                'MM13', 'MW13', 'NG13', 'NQ13', 'OA13',
                'OK13', 'OU13', 'PE13', 'PO13', 'PY13', 'QI13', 'QS13', 'RC13',
                'RM13', 'RW13', 'SG13', 'SQ13', 'TA13',
                'TK13', 'TU13', 'UE13', 'UO13', 'UY13', 'VI13', 'VS13', 'WC13',
                'WM13', 'WW13', 'XG13', 'XQ13', 'YA13',
                'YK13', 'YU13', 'ZE13', 'ZO13', 'ZY13', 'AAI13', 'AAS13',
                'ABC13',
                'ABM13', 'ABW13', 'ACG13', 'ACQ13', 'ADA13', 'ADK13', 'ADU13',
                'AEE13', 'AEO13', 'AEY13', 'AFI13', 'AFS13', 'AGC13', 'AGM13',
                'AGW13', 'AHG13', 'AHQ13', 'AIA13', 'AIK13', 'AIU13', 'AJE13',
                'AJO13', 'AJY13', 'AKI13', 'AKS13',
                'ALC13', 'ALM13', 'ALW13', 'AMG13', 'AMQ13', 'ANA13', 'ANK13']

job_name_bottom = ['K18', 'U18', 'AE18', 'AO18', 'AY18', 'BI18', 'BS18', 'CC18',
                   'CM18', 'CW18', 'DG18', 'DQ18', 'EA18',
                   'EK18', 'EU18', 'FE18', 'FO18', 'FY18', 'GI18', 'GS18',
                   'HC18',
                   'HM18', 'HW18', 'IG18', 'IQ18', 'JA18',
                   'JK18', 'JU18', 'KE18', 'KO18', 'KY18', 'LI18', 'LS18',
                   'MC18',
                   'MM18', 'MW18', 'NG18', 'NQ18', 'OA18',
                   'OK18', 'OU18', 'PE18', 'PO18', 'PY18', 'QI18', 'QS18',
                   'RC18',
                   'RM18', 'RW18', 'SG18', 'SQ18', 'TA18',
                   'TK18', 'TU18', 'UE18', 'UO18', 'UY18', 'VI18', 'VS18',
                   'WC18',
                   'WM18', 'WW18', 'XG18', 'XQ18', 'YA18',
                   'YK18', 'YU18', 'ZE18', 'ZO18', 'ZY18', 'AAI18', 'AAS18',
                   'ABC18',
                   'ABM18', 'ABW18', 'ACG18', 'ACQ18', 'ADA18', 'ADK18',
                   'ADU18', 'AEE18', 'AEO18', 'AEY18', 'AFI18', 'AFS18',
                   'AGC18', 'AGM18', 'AGW18', 'AHG18', 'AHQ18', 'AIA18',
                   'AIK18', 'AIU18', 'AJE18', 'AJO18', 'AJY18', 'AKI18',
                   'AKS18',
                   'ALC18', 'ALM18', 'ALW18', 'AMG18', 'AMQ18', 'ANA18',
                   'ANK18']

job_name_top_2 = ['U13', 'AE13', 'AO13', 'AY13', 'BI13', 'BS13', 'CC13', 'CM13',
                  'CW13', 'DG13', 'DQ13', 'EA13',
                  'EK13', 'EU13', 'FE13', 'FO13', 'FY13', 'GI13', 'GS13',
                  'HC13',
                  'HM13', 'HW13', 'IG13', 'IQ13', 'JA13',
                  'JK13', 'JU13', 'KE13', 'KO13', 'KY13', 'LI13', 'LS13',
                  'MC13',
                  'MM13', 'MW13', 'NG13', 'NQ13', 'OA13',
                  'OK13', 'OU13', 'PE13', 'PO13', 'PY13', 'QI13', 'QS13',
                  'RC13',
                  'RM13', 'RW13', 'SG13', 'SQ13', 'TA13',
                  'TK13', 'TU13', 'UE13', 'UO13', 'UY13', 'VI13', 'VS13',
                  'WC13',
                  'WM13', 'WW13', 'XG13', 'XQ13', 'YA13',
                  'YK13', 'YU13', 'ZE13', 'ZO13', 'ZY13', 'AAI13', 'AAS13',
                  'ABC13',
                  'ABM13', 'ABW13', 'ACG13', 'ACQ13', 'ADA13', 'ADK13', 'ADU13',
                  'AEE13', 'AEO13', 'AEY13', 'AFI13', 'AFS13', 'AGC13', 'AGM13',
                  'AGW13', 'AHG13', 'AHQ13', 'AIA13', 'AIK13', 'AIU13', 'AJE13',
                  'AJO13', 'AJY13', 'AKI13', 'AKS13',
                  'ALC13', 'ALM13', 'ALW13', 'AMG13', 'AMQ13', 'ANA13', 'ANK13']

job_name_bottom_2 = ['U18', 'AE18', 'AO18', 'AY18', 'BI18', 'BS18', 'CC18',
                     'CM18',
                     'CW18', 'DG18', 'DQ18', 'EA18',
                     'EK18', 'EU18', 'FE18', 'FO18', 'FY18', 'GI18', 'GS18',
                     'HC18',
                     'HM18', 'HW18', 'IG18', 'IQ18', 'JA18',
                     'JK18', 'JU18', 'KE18', 'KO18', 'KY18', 'LI18', 'LS18',
                     'MC18',
                     'MM18', 'MW18', 'NG18', 'NQ18', 'OA18',
                     'OK18', 'OU18', 'PE18', 'PO18', 'PY18', 'QI18', 'QS18',
                     'RC18',
                     'RM18', 'RW18', 'SG18', 'SQ18', 'TA18',
                     'TK18', 'TU18', 'UE18', 'UO18', 'UY18', 'VI18', 'VS18',
                     'WC18',
                     'WM18', 'WW18', 'XG18', 'XQ18', 'YA18',
                     'YK18', 'YU18', 'ZE18', 'ZO18', 'ZY18', 'AAI18', 'AAS18',
                     'ABC18',
                     'ABM18', 'ABW18', 'ACG18', 'ACQ18', 'ADA18', 'ADK18',
                     'ADU18', 'AEE18', 'AEO18', 'AEY18', 'AFI18', 'AFS18',
                     'AGC18', 'AGM18', 'AGW18', 'AHG18', 'AHQ18', 'AIA18',
                     'AIK18', 'AIU18', 'AJE18', 'AJO18', 'AJY18', 'AKI18',
                     'AKS18',
                     'ALC18', 'ALM18', 'ALW18', 'AMG18', 'AMQ18', 'ANA18',
                     'ANK18']

job_name_top_3 = ['AE13', 'AO13', 'AY13', 'BI13', 'BS13', 'CC13', 'CM13',
                  'CW13', 'DG13', 'DQ13', 'EA13',
                  'EK13', 'EU13', 'FE13', 'FO13', 'FY13', 'GI13', 'GS13',
                  'HC13',
                  'HM13', 'HW13', 'IG13', 'IQ13', 'JA13',
                  'JK13', 'JU13', 'KE13', 'KO13', 'KY13', 'LI13', 'LS13',
                  'MC13',
                  'MM13', 'MW13', 'NG13', 'NQ13', 'OA13',
                  'OK13', 'OU13', 'PE13', 'PO13', 'PY13', 'QI13', 'QS13',
                  'RC13',
                  'RM13', 'RW13', 'SG13', 'SQ13', 'TA13',
                  'TK13', 'TU13', 'UE13', 'UO13', 'UY13', 'VI13', 'VS13',
                  'WC13',
                  'WM13', 'WW13', 'XG13', 'XQ13', 'YA13',
                  'YK13', 'YU13', 'ZE13', 'ZO13', 'ZY13', 'AAI13', 'AAS13',
                  'ABC13',
                  'ABM13', 'ABW13', 'ACG13', 'ACQ13', 'ADA13', 'ADK13', 'ADU13',
                  'AEE13', 'AEO13', 'AEY13', 'AFI13', 'AFS13', 'AGC13', 'AGM13',
                  'AGW13', 'AHG13', 'AHQ13', 'AIA13', 'AIK13', 'AIU13', 'AJE13',
                  'AJO13', 'AJY13', 'AKI13', 'AKS13',
                  'ALC13', 'ALM13', 'ALW13', 'AMG13', 'AMQ13', 'ANA13', 'ANK13']

job_name_bottom_3 = ['AE18', 'AO18', 'AY18', 'BI18', 'BS18', 'CC18', 'CM18',
                     'CW18', 'DG18', 'DQ18', 'EA18',
                     'EK18', 'EU18', 'FE18', 'FO18', 'FY18', 'GI18', 'GS18',
                     'HC18',
                     'HM18', 'HW18', 'IG18', 'IQ18', 'JA18',
                     'JK18', 'JU18', 'KE18', 'KO18', 'KY18', 'LI18', 'LS18',
                     'MC18',
                     'MM18', 'MW18', 'NG18', 'NQ18', 'OA18',
                     'OK18', 'OU18', 'PE18', 'PO18', 'PY18', 'QI18', 'QS18',
                     'RC18',
                     'RM18', 'RW18', 'SG18', 'SQ18', 'TA18',
                     'TK18', 'TU18', 'UE18', 'UO18', 'UY18', 'VI18', 'VS18',
                     'WC18',
                     'WM18', 'WW18', 'XG18', 'XQ18', 'YA18',
                     'YK18', 'YU18', 'ZE18', 'ZO18', 'ZY18', 'AAI18', 'AAS18',
                     'ABC18',
                     'ABM18', 'ABW18', 'ACG18', 'ACQ18', 'ADA18', 'ADK18',
                     'ADU18', 'AEE18', 'AEO18', 'AEY18', 'AFI18', 'AFS18',
                     'AGC18', 'AGM18', 'AGW18', 'AHG18', 'AHQ18', 'AIA18',
                     'AIK18', 'AIU18', 'AJE18', 'AJO18', 'AJY18', 'AKI18',
                     'AKS18',
                     'ALC18', 'ALM18', 'ALW18', 'AMG18', 'AMQ18', 'ANA18',
                     'ANK18']

job_name_top_4 = ['AO13', 'AY13', 'BI13', 'BS13', 'CC13', 'CM13',
                  'CW13', 'DG13', 'DQ13', 'EA13',
                  'EK13', 'EU13', 'FE13', 'FO13', 'FY13', 'GI13', 'GS13',
                  'HC13',
                  'HM13', 'HW13', 'IG13', 'IQ13', 'JA13',
                  'JK13', 'JU13', 'KE13', 'KO13', 'KY13', 'LI13', 'LS13',
                  'MC13',
                  'MM13', 'MW13', 'NG13', 'NQ13', 'OA13',
                  'OK13', 'OU13', 'PE13', 'PO13', 'PY13', 'QI13', 'QS13',
                  'RC13',
                  'RM13', 'RW13', 'SG13', 'SQ13', 'TA13',
                  'TK13', 'TU13', 'UE13', 'UO13', 'UY13', 'VI13', 'VS13',
                  'WC13',
                  'WM13', 'WW13', 'XG13', 'XQ13', 'YA13',
                  'YK13', 'YU13', 'ZE13', 'ZO13', 'ZY13', 'AAI13', 'AAS13',
                  'ABC13',
                  'ABM13', 'ABW13', 'ACG13', 'ACQ13', 'ADA13', 'ADK13', 'ADU13',
                  'AEE13', 'AEO13', 'AEY13', 'AFI13', 'AFS13', 'AGC13', 'AGM13',
                  'AGW13', 'AHG13', 'AHQ13', 'AIA13', 'AIK13', 'AIU13', 'AJE13',
                  'AJO13', 'AJY13', 'AKI13', 'AKS13',
                  'ALC13', 'ALM13', 'ALW13', 'AMG13', 'AMQ13', 'ANA13', 'ANK13']

job_name_bottom_4 = ['AO18', 'AY18', 'BI18', 'BS18', 'CC18', 'CM18',
                     'CW18', 'DG18', 'DQ18', 'EA18',
                     'EK18', 'EU18', 'FE18', 'FO18', 'FY18', 'GI18', 'GS18',
                     'HC18',
                     'HM18', 'HW18', 'IG18', 'IQ18', 'JA18',
                     'JK18', 'JU18', 'KE18', 'KO18', 'KY18', 'LI18', 'LS18',
                     'MC18',
                     'MM18', 'MW18', 'NG18', 'NQ18', 'OA18',
                     'OK18', 'OU18', 'PE18', 'PO18', 'PY18', 'QI18', 'QS18',
                     'RC18',
                     'RM18', 'RW18', 'SG18', 'SQ18', 'TA18',
                     'TK18', 'TU18', 'UE18', 'UO18', 'UY18', 'VI18', 'VS18',
                     'WC18',
                     'WM18', 'WW18', 'XG18', 'XQ18', 'YA18',
                     'YK18', 'YU18', 'ZE18', 'ZO18', 'ZY18', 'AAI18', 'AAS18',
                     'ABC18',
                     'ABM18', 'ABW18', 'ACG18', 'ACQ18', 'ADA18', 'ADK18',
                     'ADU18', 'AEE18', 'AEO18', 'AEY18', 'AFI18', 'AFS18',
                     'AGC18', 'AGM18', 'AGW18', 'AHG18', 'AHQ18', 'AIA18',
                     'AIK18', 'AIU18', 'AJE18', 'AJO18', 'AJY18', 'AKI18',
                     'AKS18',
                     'ALC18', 'ALM18', 'ALW18', 'AMG18', 'AMQ18', 'ANA18',
                     'ANK18']

job_name_top_5 = ['AY13', 'BI13', 'BS13', 'CC13', 'CM13',
                  'CW13', 'DG13', 'DQ13', 'EA13',
                  'EK13', 'EU13', 'FE13', 'FO13', 'FY13', 'GI13', 'GS13',
                  'HC13',
                  'HM13', 'HW13', 'IG13', 'IQ13', 'JA13',
                  'JK13', 'JU13', 'KE13', 'KO13', 'KY13', 'LI13', 'LS13',
                  'MC13',
                  'MM13', 'MW13', 'NG13', 'NQ13', 'OA13',
                  'OK13', 'OU13', 'PE13', 'PO13', 'PY13', 'QI13', 'QS13',
                  'RC13',
                  'RM13', 'RW13', 'SG13', 'SQ13', 'TA13',
                  'TK13', 'TU13', 'UE13', 'UO13', 'UY13', 'VI13', 'VS13',
                  'WC13',
                  'WM13', 'WW13', 'XG13', 'XQ13', 'YA13',
                  'YK13', 'YU13', 'ZE13', 'ZO13', 'ZY13', 'AAI13', 'AAS13',
                  'ABC13',
                  'ABM13', 'ABW13', 'ACG13', 'ACQ13', 'ADA13', 'ADK13', 'ADU13',
                  'AEE13', 'AEO13', 'AEY13', 'AFI13', 'AFS13', 'AGC13', 'AGM13',
                  'AGW13', 'AHG13', 'AHQ13', 'AIA13', 'AIK13', 'AIU13', 'AJE13',
                  'AJO13', 'AJY13', 'AKI13', 'AKS13',
                  'ALC13', 'ALM13', 'ALW13', 'AMG13', 'AMQ13', 'ANA13', 'ANK13']

job_name_bottom_5 = ['AY18', 'BI18', 'BS18', 'CC18', 'CM18',
                     'CW18', 'DG18', 'DQ18', 'EA18',
                     'EK18', 'EU18', 'FE18', 'FO18', 'FY18', 'GI18', 'GS18',
                     'HC18',
                     'HM18', 'HW18', 'IG18', 'IQ18', 'JA18',
                     'JK18', 'JU18', 'KE18', 'KO18', 'KY18', 'LI18', 'LS18',
                     'MC18',
                     'MM18', 'MW18', 'NG18', 'NQ18', 'OA18',
                     'OK18', 'OU18', 'PE18', 'PO18', 'PY18', 'QI18', 'QS18',
                     'RC18',
                     'RM18', 'RW18', 'SG18', 'SQ18', 'TA18',
                     'TK18', 'TU18', 'UE18', 'UO18', 'UY18', 'VI18', 'VS18',
                     'WC18',
                     'WM18', 'WW18', 'XG18', 'XQ18', 'YA18',
                     'YK18', 'YU18', 'ZE18', 'ZO18', 'ZY18', 'AAI18', 'AAS18',
                     'ABC18',
                     'ABM18', 'ABW18', 'ACG18', 'ACQ18', 'ADA18', 'ADK18',
                     'ADU18', 'AEE18', 'AEO18', 'AEY18', 'AFI18', 'AFS18',
                     'AGC18', 'AGM18', 'AGW18', 'AHG18', 'AHQ18', 'AIA18',
                     'AIK18', 'AIU18', 'AJE18', 'AJO18', 'AJY18', 'AKI18',
                     'AKS18',
                     'ALC18', 'ALM18', 'ALW18', 'AMG18', 'AMQ18', 'ANA18',
                     'ANK18']

job_name_top_6 = ['BI13', 'BS13', 'CC13', 'CM13',
                  'CW13', 'DG13', 'DQ13', 'EA13',
                  'EK13', 'EU13', 'FE13', 'FO13', 'FY13', 'GI13', 'GS13',
                  'HC13',
                  'HM13', 'HW13', 'IG13', 'IQ13', 'JA13',
                  'JK13', 'JU13', 'KE13', 'KO13', 'KY13', 'LI13', 'LS13',
                  'MC13',
                  'MM13', 'MW13', 'NG13', 'NQ13', 'OA13',
                  'OK13', 'OU13', 'PE13', 'PO13', 'PY13', 'QI13', 'QS13',
                  'RC13',
                  'RM13', 'RW13', 'SG13', 'SQ13', 'TA13',
                  'TK13', 'TU13', 'UE13', 'UO13', 'UY13', 'VI13', 'VS13',
                  'WC13',
                  'WM13', 'WW13', 'XG13', 'XQ13', 'YA13',
                  'YK13', 'YU13', 'ZE13', 'ZO13', 'ZY13', 'AAI13', 'AAS13',
                  'ABC13',
                  'ABM13', 'ABW13', 'ACG13', 'ACQ13', 'ADA13', 'ADK13', 'ADU13',
                  'AEE13', 'AEO13', 'AEY13', 'AFI13', 'AFS13', 'AGC13', 'AGM13',
                  'AGW13', 'AHG13', 'AHQ13', 'AIA13', 'AIK13', 'AIU13', 'AJE13',
                  'AJO13', 'AJY13', 'AKI13', 'AKS13',
                  'ALC13', 'ALM13', 'ALW13', 'AMG13', 'AMQ13', 'ANA13', 'ANK13']

job_name_bottom_6 = ['BI18', 'BS18', 'CC18', 'CM18',
                     'CW18', 'DG18', 'DQ18', 'EA18',
                     'EK18', 'EU18', 'FE18', 'FO18', 'FY18', 'GI18', 'GS18',
                     'HC18',
                     'HM18', 'HW18', 'IG18', 'IQ18', 'JA18',
                     'JK18', 'JU18', 'KE18', 'KO18', 'KY18', 'LI18', 'LS18',
                     'MC18',
                     'MM18', 'MW18', 'NG18', 'NQ18', 'OA18',
                     'OK18', 'OU18', 'PE18', 'PO18', 'PY18', 'QI18', 'QS18',
                     'RC18',
                     'RM18', 'RW18', 'SG18', 'SQ18', 'TA18',
                     'TK18', 'TU18', 'UE18', 'UO18', 'UY18', 'VI18', 'VS18',
                     'WC18',
                     'WM18', 'WW18', 'XG18', 'XQ18', 'YA18',
                     'YK18', 'YU18', 'ZE18', 'ZO18', 'ZY18', 'AAI18', 'AAS18',
                     'ABC18',
                     'ABM18', 'ABW18', 'ACG18', 'ACQ18', 'ADA18', 'ADK18',
                     'ADU18', 'AEE18', 'AEO18', 'AEY18', 'AFI18', 'AFS18',
                     'AGC18', 'AGM18', 'AGW18', 'AHG18', 'AHQ18', 'AIA18',
                     'AIK18', 'AIU18', 'AJE18', 'AJO18', 'AJY18', 'AKI18',
                     'AKS18',
                     'ALC18', 'ALM18', 'ALW18', 'AMG18', 'AMQ18', 'ANA18',
                     'ANK18']

comp_list = ['A2', 'B2', 'C2', 'D2', 'E2', 'F2', 'G2', 'H2', 'I2', 'J2', 'K2',
             'L2', 'M2',
             'N2', 'O2', 'P2', 'Q2', 'R2', 'S2', 'T2', 'U2', 'V2', 'W2', 'X2',
             'Y2', 'Z2',
             'AA2', 'AB2', 'AC2', 'AD2', 'AE2', 'AF2', 'AG2', 'AH2', 'AI2',
             'AJ2', 'AK2', 'AL2', 'AM2', 'AN2']

pic_4 = [["L10", "Q10", "L15", "Q15"], ["V10", "AA10", "V15", "AA15"],
         ["AF10", "AK10", "AF15", "AK15"], ["AP10", "AU10", "AP15", "AU15"],
         ["AZ10", "BE10", "AZ15", "BE15"],
         ["BJ10", "BO10", "BJ15", "BO15"], ["BT10", "BY10", "BT15", "BY15"],
         ["CD10", "CI10", "CD15", "CI15"], ["CN10", "CS10", "CN15", "CS15"],
         ["CX10", "DC10", "CX15", "DC15"],
         ["DH10", "DM10", "DH15", "DM15"], ["DR10", "DW10", "DR15", "DW15"],
         ["EB10", "EG10", "EB15", "EG15"], ["EL10", "EQ10", "EL15", "EQ15"],
         ["EV10", "FA10", "EV15", "FA15"],
         ["FF10", "FK10", "FF15", "FK15"], ["FP10", "FU10", "FP15", "FU15"],
         ["FZ10", "GE10", "FZ15", "GE15"], ["GJ10", "GO10", "GJ15", "GO15"],
         ["GT10", "GY10", "GT15", "GY15"],
         ["HD10", "HI10", "HD15", "HI15"], ["HN10", "HS10", "HN15", "HS15"],
         ["HX10", "IC10", "HX15", "IC15"], ["IH10", "IM10", "IH15", "IM15"],
         ["IR10", "IW10", "IR15", "IW15"],
         ["JB10", "JG10", "JB15", "JG15"], ["JL10", "JQ10", "JL15", "JQ15"],
         ["JV10", "KA10", "JV15", "KA15"], ["KF10", "KK10", "KF15", "KK15"],
         ["KP10", "KU10", "KP15", "KU15"],
         ["KZ10", "LE10", "KZ15", "LE15"], ["LJ10", "LO10", "LJ15", "LO15"],
         ["LT10", "LY10", "LT15", "LY15"], ["MD10", "MI10", "MD15", "MI15"],
         ["MN10", "MS10", "MN15", "MS15"],
         ["MX10", "NC10", "MX15", "NC15"], ["NH10", "NM10", "NH15", "NM15"],
         ["NR10", "NW10", "NR15", "NW15"], ["OB10", "OG10", "OB15", "OG15"],
         ["OL10", "OQ10", "OL15", "OQ15"],
         ["OV10", "PA10", "OV15", "PA15"], ["PF10", "PK10", "PF15", "PK15"],
         ["PP10", "PU10", "PP15", "PU15"], ["PZ10", "QE10", "PZ15", "QE15"],
         ["QJ10", "QO10", "QJ15", "QO15"],
         ["QT10", "QY10", "QT15", "QY15"], ["RD10", "RI10", "RD15", "RI15"],
         ["RN10", "RS10", "RN15", "RS15"], ["RX10", "SC10", "RX15", "SC15"],
         ["SH10", "SM10", "SH15", "SM15"],
         ["SR10", "SW10", "SR15", "SW15"], ["TB10", "TG10", "TB15", "TG15"],
         ["TL10", "TQ10", "TL15", "TQ15"], ["TV10", "UA10", "TV15", "UA15"],
         ["UF10", "UK10", "UF15", "UK15"],
         ["UP10", "UU10", "UP15", "UU15"], ["UZ10", "VE10", "UZ15", "VE15"],
         ["VJ10", "VO10", "VJ15", "VO15"], ["VT10", "VY10", "VT15", "VY15"],
         ["WD10", "WI10", "WD15", "WI15"],
         ["WN10", "WS10", "WN15", "WS15"], ["WX10", "XC10", "WX15", "XC15"],
         ["XH10", "XM10", "XH15", "XM15"], ["XR10", "XW10", "XR15", "XW15"],
         ["YB10", "YG10", "YB15", "YG15"],
         ["YL10", "YQ10", "YL15", "YQ15"], ["YV10", "ZA10", "YV15", "ZA15"],
         ["ZF10", "ZK10", "ZF15", "ZK15"], ["ZP10", "ZU10", "ZP15", "ZU15"],
         ["ZZ10", "AAE10", "ZZ15", "AAE15"],
         ["AAJ10", "AAO10", "AAJ15", "AAO15"],
         ["AAT10", "AAY10", "AAT15", "AAY15"],
         ["ABD10", "ABI10", "ABD15", "ABI15"],
         ['ABN10', 'ABS10', 'ABN15', 'ABS15'],
         ['ABX10', 'ACC10', 'ABX15', 'ACC15'],
         ['ACH10', 'ACM10', 'ACH15', 'ACM15'],
         ['ACR10', 'ACW10', 'ACR15', 'ACW10'],
         ['ADB10', 'ADG10', 'ADB15', 'ADG15'],
         ['ADL10', 'ADQ10', 'ADL15', 'ADQ15'],
         ['ADV10', 'AEA10', 'ADV15', 'AEA15'],
         ['AEF10', 'AEK10', 'AEF15', 'AEK15'],
         ['AEP10', 'AEU10', 'AEP15', 'AEU15'],
         ['AEZ10', 'AFE10', 'AEZ15', 'AFE15'],
         ['AFJ10', 'AFO10', 'AFJ15', 'AFO15'],
         ['AFT10', 'AFY10', 'AFT15', 'AFY15'],
         ['AGD10', 'AGI10', 'AGD15', 'AGI15'],
         ['AGN10', 'AGS10', 'AGN15', 'AGS15'],
         ['AGX10', 'AHC10', 'AGX15', 'AHC15'],
         ['AHH10', 'AHM10', 'AHH15', 'AHM15'],
         ['AHR10', 'AHW10', 'AHR15', 'AHW15'],
         ['AIB10', 'AIG10', 'AIB15', 'AIG15'],
         ['AIL10', 'AIQ10', 'AIL15', 'AIQ15'],
         ['AIV10', 'AJA10', 'AIV15', 'AJA15'],
         ['AJF10', 'AJK10', 'AJF15', 'AJK15'],
         ['AJP10', 'AJU10', 'AJP15', 'AJU15'],
         ['AJZ10', 'AKE10', 'AJZ15', 'AKE15'],
         ['AKJ10', 'AKO10', 'AKJ15', 'AKO15'],
         ['AKT10', 'AKY10', 'AKT15', 'AKY15'],
         ['ALD10', 'ALI10', 'ALD15', 'ALI15'],
         ['ALN10', 'ALS10', 'ALN15', 'ALS15'],
         ['ALX10', 'AMC10', 'ALX15', 'AMC15'],
         ['AMH10', 'AMM10', 'AMH15', 'AMM15'],
         ['AMR10', 'AMW10', 'AMR15', 'AMW15'],
         ['ANB10', 'ANG10', 'ANB15', 'ANG15']]

pic_3 = [["L10", "L15", "Q15"], ["V10", "V15", "AA15"],
         ["AF10", "AF15", "AK15"], ["AP10", "AP15", "AU15"],
         ["AZ10", "AZ15", "BE15"],
         ["BJ10", "BJ15", "BO15"], ["BT10", "BT15", "BY15"],
         ["CD10", "CD15", "CI15"], ["CN10", "CN15", "CS15"],
         ["CX10", "CX15", "DC15"],
         ["DH10", "DH15", "DM15"], ["DR10", "DR15", "DW15"],
         ["EB10", "EB15", "EG15"], ["EL10", "EL15", "EQ15"],
         ["EV10", "EV15", "FA15"],
         ["FF10", "FF15", "FK15"], ["FP10", "FP15", "FU15"],
         ["FZ10", "FZ15", "GE15"], ["GJ10", "GJ15", "GO15"],
         ["GT10", "GT15", "GY15"],
         ["HD10", "HD15", "HI15"], ["HN10", "HN15", "HS15"],
         ["HX10", "HX15", "IC15"], ["IH10", "IH15", "IM15"],
         ["IR10", "IR15", "IW15"],
         ["JB10", "JB15", "JG15"], ["JL10", "JL15", "JQ15"],
         ["JV10", "JV15", "KA15"], ["KF10", "KF15", "KK15"],
         ["KP10", "KP15", "KU15"],
         ["KZ10", "KZ15", "LE15"], ["LJ10", "LJ15", "LO15"],
         ["LT10", "LT15", "LY15"], ["MD10", "MD15", "MI15"],
         ["MN10", "MN15", "MS15"],
         ["MX10", "MX15", "NC15"], ["NH10", "NH15", "NM15"],
         ["NR10", "NR15", "NW15"], ["OB10", "OB15", "OG15"],
         ["OL10", "OL15", "OQ15"],
         ["OV10", "OV15", "PA15"], ["PF10", "PF15", "PK15"],
         ["PP10", "PP15", "PU15"], ["PZ10", "PZ15", "QE15"],
         ["QJ10", "QJ15", "QO15"],
         ["QT10", "QT15", "QY15"], ["RD10", "RD15", "RI15"],
         ["RN10", "RN15", "RS15"], ["RX10", "RX15", "SC15"],
         ["SH10", "SH15", "SM15"],
         ["SR10", "SR15", "SW15"], ["TB10", "TB15", "TG15"],
         ["TL10", "TL15", "TQ15"], ["TV10", "TV15", "UA15"],
         ["UF10", "UF15", "UK15"],
         ["UP10", "UP15", "UU15"], ["UZ10", "UZ15", "VE15"],
         ["VJ10", "VJ15", "VO15"], ["VT10", "VT15", "VY15"],
         ["WD10", "WD15", "WI15"],
         ["WN10", "WN15", "WS15"], ["WX10", "WX15", "XC15"],
         ["XH10", "XH15", "XM15"], ["XR10", "XR15", "XW15"],
         ["YB10", "YB15", "YG15"],
         ["YL10", "YL15", "YQ15"], ["YV10", "YV15", "ZA15"],
         ["ZF10", "ZF15", "ZK15"], ["ZP10", "ZP15", "ZU15"],
         ["ZZ10", "ZZ15", "AAE15"], ["AAJ10", "AAJ15", "AAO15"],
         ["AAT10", "AAT15", "AAY15"], ["ABD10", "ABD15", "ABI15"],
         ['ABN10', 'ABN15', 'ABS15'], ['ABX10', 'ABX15', 'ACC15'],
         ['ACH10', 'ACH15', 'ACM15'],
         ['ACR10', 'ACR15', 'ACW10'], ['ADB10', 'ADB15', 'ADG15'],
         ['ADL10', 'ADL15', 'ADQ15'], ['ADV10', 'ADV15', 'AEA15'],
         ['AEF10', 'AEF15', 'AEK15'], ['AEP10', 'AEP15', 'AEU15'],
         ['AEZ10', 'AEZ15', 'AFE15'], ['AFJ10', 'AFJ15', 'AFO15'],
         ['AFT10', 'AFT15', 'AFY15'], ['AGD10', 'AGD15', 'AGI15'],
         ['AGN10', 'AGN15', 'AGS15'], ['AGX10', 'AGX15', 'AHC15'],
         ['AHH10', 'AHH15', 'AHM15'], ['AHR10', 'AHR15', 'AHW15'],
         ['AIB10', 'AIB15', 'AIG15'], ['AIL10', 'AIL15', 'AIQ15'],
         ['AIV10', 'AIV15', 'AJA15'], ['AJF10', 'AJF15', 'AJK15'],
         ['AJP10', 'AJP15', 'AJU15'], ['AJZ10', 'AJZ15', 'AKE15'],
         ['AKJ10', 'AKJ15', 'AKO15'], ['AKT10', 'AKT15', 'AKY15'],
         ['ALD10', 'ALD15', 'ALI15'], ['ALN10', 'ALN15', 'ALS15'],
         ['ALX10', 'ALX15', 'AMC15'], ['AMH10', 'AMH15', 'AMM15'],
         ['AMR10', 'AMR15', 'AMW15'], ['ANB10', 'ANB15', 'ANG15'],
         ['ANL10', 'ANL15', 'ANG15']]

pic_2 = [["L10", "Q10"], ["V10", "AA10"], ["AF10", "AK10"], ["AP10", "AU10"],
         ["AZ10", "BE10"],
         ["BJ10", "BO10"], ["BT10", "BY10"], ["CD10", "CI10"], ["CN10", "CS10"],
         ["CX10", "DC10"],
         ["DH10", "DM10"], ["DR10", "DW10"], ["EB10", "EG10"], ["EL10", "EQ10"],
         ["EV10", "FA10"],
         ["FF10", "FK10"], ["FP10", "FU10"], ["FZ10", "GE10"], ["GJ10", "GO10"],
         ["GT10", "GY10"],
         ["HD10", "HI10"], ["HN10", "HS10"], ["HX10", "IC10"], ["IH10", "IM10"],
         ["IR10", "IW10"],
         ["JB10", "JG10"], ["JL10", "JQ10"], ["JV10", "KA10"], ["KF10", "KK10"],
         ["KP10", "KU10"],
         ["KZ10", "LE10"], ["LJ10", "LO10"], ["LT10", "LY10"], ["MD10", "MI10"],
         ["MN10", "MS10"],
         ["MX10", "NC10"], ["NH10", "NM10"], ["NR10", "NW10"], ["OB10", "OG10"],
         ["OL10", "OQ10"],
         ["OV10", "PA10"], ["PF10", "PK10"], ["PP10", "PU10"], ["PZ10", "QE10"],
         ["QJ10", "QO10"],
         ["QT10", "QY10"], ["RD10", "RI10"], ["RN10", "RS10"], ["RX10", "SC10"],
         ["SH10", "SM10"],
         ["SR10", "SW10"], ["TB10", "TG10"], ["TL10", "TQ10"], ["TV10", "UA10"],
         ["UF10", "UK10"],
         ["UP10", "UU10"], ["UZ10", "VE10"], ["VJ10", "VO10"], ["VT10", "VY10"],
         ["WD10", "WI10"],
         ["WN10", "WS10"], ["WX10", "XC10"], ["XH10", "XM10"], ["XR10", "XW10"],
         ["YB10", "YG10"],
         ["YL10", "YQ10"], ["YV10", "ZA10"], ["ZF10", "ZK10"], ["ZP10", "ZU10"],
         ["ZZ10", "AAE10"], ["AAJ10", "AAO10"], ["AAT10", "AAY10"],
         ["ABD10", "ABI10"],
         ['ABN10', 'ABS10'], ['ABX10', 'ACC10'],
         ['ACH10', 'ACM10'],
         ['ACR10', 'ACW10'], ['ADB10', 'ADG10'],
         ['ADL10', 'ADQ10'], ['ADV10', 'AEA10'],
         ['AEF10', 'AEK10'], ['AEP10', 'AEU10'],
         ['AEZ10', 'AFE10'], ['AFJ10', 'AFO10'],
         ['AFT10', 'AFY10'], ['AGD10', 'AGI10'],
         ['AGN10', 'AGS10'], ['AGX10', 'AHC10'],
         ['AHH10', 'AHM10'], ['AHR10', 'AHW10'],
         ['AIB10', 'AIG10'], ['AIL10', 'AIQ10'],
         ['AIV10', 'AJA10'], ['AJF10', 'AJK10'],
         ['AJP10', 'AJU10'], ['AJZ10', 'AKE10'],
         ['AKJ10', 'AKO10'], ['AKT10', 'AKY10'],
         ['ALD10', 'ALI10'], ['ALN10', 'ALS10'],
         ['ALX10', 'AMC10'], ['AMH10', 'AMM10'],
         ['AMR10', 'AMW10'], ['ANB10', 'ANG10']]

pic_2_merged = [["L15", "Q15"], ["V15", "AA15"], ["AF15", "AK15"],
                ["AP15", "AU15"], ["AZ15", "BE15"],
                ["BJ15", "BO15"], ["BT15", "BY15"], ["CD15", "CI15"],
                ["CN15", "CS15"], ["CX15", "DC15"],
                ["DH15", "DM15"], ["DR15", "DW15"], ["EB15", "EG15"],
                ["EL15", "EQ15"], ["EV15", "FA15"],
                ["FF15", "FK15"], ["FP15", "FU15"], ["FZ15", "GE15"],
                ["GJ15", "GO15"], ["GT15", "GY15"],
                ["HD15", "HI15"], ["HN15", "HS15"], ["HX15", "IC15"],
                ["IH15", "IM15"], ["IR15", "IW15"],
                ["JB15", "JG15"], ["JL15", "JQ15"], ["JV15", "KA15"],
                ["KF15", "KK15"], ["KP15", "KU15"],
                ["KZ15", "LE15"], ["LJ15", "LO15"], ["LT15", "LY15"],
                ["MD15", "MI15"], ["MN15", "MS15"],
                ["MX15", "NC15"], ["NH15", "NM15"], ["NR15", "NW15"],
                ["OB15", "OG15"], ["OL15", "OQ15"],
                ["OV15", "PA15"], ["PF15", "PK15"], ["PP15", "PU15"],
                ["PZ15", "QE15"], ["QJ15", "QO15"],
                ["QT15", "QY15"], ["RD15", "RI15"], ["RN15", "RS15"],
                ["RX15", "SC15"], ["SH15", "SM15"],
                ["SR15", "SW15"], ["TB15", "TG15"], ["TL15", "TQ15"],
                ["TV15", "UA15"], ["UF15", "UK15"],
                ["UP15", "UU15"], ["UZ15", "VE15"], ["VJ15", "VO15"],
                ["VT15", "VY15"], ["WD15", "WI15"],
                ["WN15", "WS15"], ["WX15", "XC15"], ["XH15", "XM15"],
                ["XR15", "XW15"], ["YB15", "YG15"],
                ["YL15", "YQ15"], ["YV15", "ZA15"], ["ZF15", "ZK15"],
                ["ZP15", "ZU15"], ["ZZ15", "AAE15"], ["AAJ15", "AAO15"],
                ["AAT15", "AAY15"], ["ABD15", "ABI15"],
                ['ABN15', 'ABS15'], ['ABX15', 'ACC15'],
                ['ACH15', 'ACM15'],
                ['ACR15', 'ACW15'], ['ADB15', 'ADG15'],
                ['ADL15', 'ADQ15'], ['ADV15', 'AEA15'],
                ['AEF15', 'AEK15'], ['AEP15', 'AEU15'],
                ['AEZ15', 'AFE15'], ['AFJ15', 'AFO15'],
                ['AFT15', 'AFY15'], ['AGD15', 'AGI15'],
                ['AGN15', 'AGS15'], ['AGX15', 'AHC15'],
                ['AHH15', 'AHM15'], ['AHR15', 'AHW15'],
                ['AIB15', 'AIG15'], ['AIL15', 'AIQ15'],
                ['AIV15', 'AJA15'], ['AJF15', 'AJK15'],
                ['AJP15', 'AJU15'], ['AJZ15', 'AKE15'],
                ['AKJ15', 'AKO15'], ['AKT15', 'AKY15'],
                ['ALD15', 'ALI15'], ['ALN15', 'ALS15'],
                ['ALX15', 'AMC15'], ['AMH15', 'AMM15'],
                ['AMR15', 'AMW15']]

pic_1 = [["Q10", "Q15"], ["AA10", "AA15"], ["AK10", "AK15"], ["AU10", "AU15"],
         ["BE10", "BE15"],
         ["BO10", "BO15"], ["BY10", "BY15"], ["CI10", "CI15"], ["CS10", "CS15"],
         ["DC10", "DC15"],
         ["DM10", "DM15"], ["DW10", "DW15"], ["EG10", "EG15"], ["EQ10", "EQ15"],
         ["FA10", "FA15"],
         ["FK10", "FK15"], ["FU10", "FU15"], ["GE10", "GE15"], ["GO10", "GO15"],
         ["GY10", "GY15"],
         ["HI10", "HI15"], ["HS10", "HS15"], ["IC10", "IC15"], ["IM10", "IM15"],
         ["IW10", "IW15"],
         ["JG10", "JG15"], ["JQ10", "JQ15"], ["KA10", "KA15"], ["KK10", "KK15"],
         ["KU10", "KU15"],
         ["LE10", "LE15"], ["LO10", "LO15"], ["LY10", "LY15"], ["MI10", "MI15"],
         ["MS10", "MS15"],
         ["NC10", "NC15"], ["NM10", "NM15"], ["NW10", "NW15"], ["OG10", "OG15"],
         ["OQ10", "OQ15"],
         ["PA10", "PA15"], ["PK10", "PK15"], ["PU10", "PU15"], ["QE10", "QE15"],
         ["QO10", "QO15"],
         ["QY10", "QY15"], ["RI10", "RI15"], ["RS10", "RS15"], ["SC10", "SC15"],
         ["SM10", "SM15"],
         ["SW10", "SW15"], ["TG10", "TG15"], ["TQ10", "TQ15"], ["UA10", "UA15"],
         ["UK10", "UK15"],
         ["UU10", "UU15"], ["VE10", "VE15"], ["VO10", "VO15"], ["VY10", "VY15"],
         ["WI10", "WI15"],
         ["WS10", "WS15"], ["XC10", "XC15"], ["XM10", "XM15"], ["XW10", "XW15"],
         ["YG10", "YG15"],
         ["YQ10", "YQ15"], ["ZA10", "ZA15"], ["ZK10", "ZK15"], ["ZU10", "ZU15"],
         ["AAE10", "AAE15"], ["AAO10", "AAO15"], ["AAY10", "AAY15"],
         ["ABI10", "ABI15"],
         ['ABS10', 'ABS15'], ['ACC10', 'ACC15'],
         ['ACM10', 'ACM15'],
         ['ACW10', 'ACW15'], ['ADG10', 'ADG15'],
         ['ADQ10', 'ADQ15'], ['AEA10', 'AEA15'],
         ['AEK10', 'AEK15'], ['AEU10', 'AEU15'],
         ['AFE10', 'AFE15'], ['AFO10', 'AFO15'],
         ['AFY10', 'AFY15'], ['AGI10', 'AGI15'],
         ['AGS10', 'AGS15'], ['AHC10', 'AHC15'],
         ['AHM10', 'AHM15'], ['AHW10', 'AHW15'],
         ['AIG10', 'AIG15'], ['AIQ10', 'AIQ15'],
         ['AJA10', 'AJA15'], ['AJK10', 'AJK15'],
         ['AJU10', 'AJU15'], ['AKE10', 'AKE15'],
         ['AKO10', 'AKO15'], ['AKY10', 'AKY15'],
         ['ALI10', 'ALI15'], ['ALS10', 'ALS15'],
         ['AMC10', 'AMC15'], ['AMM10', 'AMM15'],
         ['AMW10', 'AMW15'], ['ANG10', 'ANG15']]

pic_4_2 = [["V10", "AA10", "V15", "AA15"], ["AF10", "AK10", "AF15", "AK15"],
           ["AP10", "AU10", "AP15", "AU15"], ["AZ10", "BE10", "AZ15", "BE15"],
           ["BJ10", "BO10", "BJ15", "BO15"], ["BT10", "BY10", "BT15", "BY15"],
           ["CD10", "CI10", "CD15", "CI15"], ["CN10", "CS10", "CN15", "CS15"],
           ["CX10", "DC10", "CX15", "DC15"],
           ["DH10", "DM10", "DH15", "DM15"], ["DR10", "DW10", "DR15", "DW15"],
           ["EB10", "EG10", "EB15", "EG15"], ["EL10", "EQ10", "EL15", "EQ15"],
           ["EV10", "FA10", "EV15", "FA15"],
           ["FF10", "FK10", "FF15", "FK15"], ["FP10", "FU10", "FP15", "FU15"],
           ["FZ10", "GE10", "FZ15", "GE15"], ["GJ10", "GO10", "GJ15", "GO15"],
           ["GT10", "GY10", "GT15", "GY15"],
           ["HD10", "HI10", "HD15", "HI15"], ["HN10", "HS10", "HN15", "HS15"],
           ["HX10", "IC10", "HX15", "IC15"], ["IH10", "IM10", "IH15", "IM15"],
           ["IR10", "IW10", "IR15", "IW15"],
           ["JB10", "JG10", "JB15", "JG15"], ["JL10", "JQ10", "JL15", "JQ15"],
           ["JV10", "KA10", "JV15", "KA15"], ["KF10", "KK10", "KF15", "KK15"],
           ["KP10", "KU10", "KP15", "KU15"],
           ["KZ10", "LE10", "KZ15", "LE15"], ["LJ10", "LO10", "LJ15", "LO15"],
           ["LT10", "LY10", "LT15", "LY15"], ["MD10", "MI10", "MD15", "MI15"],
           ["MN10", "MS10", "MN15", "MS15"],
           ["MX10", "NC10", "MX15", "NC15"], ["NH10", "NM10", "NH15", "NM15"],
           ["NR10", "NW10", "NR15", "NW15"], ["OB10", "OG10", "OB15", "OG15"],
           ["OL10", "OQ10", "OL15", "OQ15"],
           ["OV10", "PA10", "OV15", "PA15"], ["PF10", "PK10", "PF15", "PK15"],
           ["PP10", "PU10", "PP15", "PU15"], ["PZ10", "QE10", "PZ15", "QE15"],
           ["QJ10", "QO10", "QJ15", "QO15"],
           ["QT10", "QY10", "QT15", "QY15"], ["RD10", "RI10", "RD15", "RI15"],
           ["RN10", "RS10", "RN15", "RS15"], ["RX10", "SC10", "RX15", "SC15"],
           ["SH10", "SM10", "SH15", "SM15"],
           ["SR10", "SW10", "SR15", "SW15"], ["TB10", "TG10", "TB15", "TG15"],
           ["TL10", "TQ10", "TL15", "TQ15"], ["TV10", "UA10", "TV15", "UA15"],
           ["UF10", "UK10", "UF15", "UK15"],
           ["UP10", "UU10", "UP15", "UU15"], ["UZ10", "VE10", "UZ15", "VE15"],
           ["VJ10", "VO10", "VJ15", "VO15"], ["VT10", "VY10", "VT15", "VY15"],
           ["WD10", "WI10", "WD15", "WI15"],
           ["WN10", "WS10", "WN15", "WS15"], ["WX10", "XC10", "WX15", "XC15"],
           ["XH10", "XM10", "XH15", "XM15"], ["XR10", "XW10", "XR15", "XW15"],
           ["YB10", "YG10", "YB15", "YG15"],
           ["YL10", "YQ10", "YL15", "YQ15"], ["YV10", "ZA10", "YV15", "ZA15"],
           ["ZF10", "ZK10", "ZF15", "ZK15"], ["ZP10", "ZU10", "ZP15", "ZU15"],
           ["ZZ10", "AAE10", "ZZ15", "AAE15"],
           ["AAJ10", "AAO10", "AAJ15", "AAO15"],
           ["AAT10", "AAY10", "AAT15", "AAY15"],
           ["ABD10", "ABI10", "ABD15", "ABI15"],
           ['ABN10', 'ABS10', 'ABN15', 'ABS15'],
           ['ABX10', 'ACC10', 'ABX15', 'ACC15'],
           ['ACH10', 'ACM10', 'ACH15', 'ACM15'],
           ['ACR10', 'ACW10', 'ACR15', 'ACW10'],
           ['ADB10', 'ADG10', 'ADB15', 'ADG15'],
           ['ADL10', 'ADQ10', 'ADL15', 'ADQ15'],
           ['ADV10', 'AEA10', 'ADV15', 'AEA15'],
           ['AEF10', 'AEK10', 'AEF15', 'AEK15'],
           ['AEP10', 'AEU10', 'AEP15', 'AEU15'],
           ['AEZ10', 'AFE10', 'AEZ15', 'AFE15'],
           ['AFJ10', 'AFO10', 'AFJ15', 'AFO15'],
           ['AFT10', 'AFY10', 'AFT15', 'AFY15'],
           ['AGD10', 'AGI10', 'AGD15', 'AGI15'],
           ['AGN10', 'AGS10', 'AGN15', 'AGS15'],
           ['AGX10', 'AHC10', 'AGX15', 'AHC15'],
           ['AHH10', 'AHM10', 'AHH15', 'AHM15'],
           ['AHR10', 'AHW10', 'AHR15', 'AHW15'],
           ['AIB10', 'AIG10', 'AIB15', 'AIG15'],
           ['AIL10', 'AIQ10', 'AIL15', 'AIQ15'],
           ['AIV10', 'AJA10', 'AIV15', 'AJA15'],
           ['AJF10', 'AJK10', 'AJF15', 'AJK15'],
           ['AJP10', 'AJU10', 'AJP15', 'AJU15'],
           ['AJZ10', 'AKE10', 'AJZ15', 'AKE15'],
           ['AKJ10', 'AKO10', 'AKJ15', 'AKO15'],
           ['AKT10', 'AKY10', 'AKT15', 'AKY15'],
           ['ALD10', 'ALI10', 'ALD15', 'ALI15'],
           ['ALN10', 'ALS10', 'ALN15', 'ALS15'],
           ['ALX10', 'AMC10', 'ALX15', 'AMC15'],
           ['AMH10', 'AMM10', 'AMH15', 'AMM15'],
           ['AMR10', 'AMW10', 'AMR15', 'AMW15'],
           ['ANB10', 'ANG10', 'ANB15', 'ANG15']]

pic_3_2 = [["V10", "V15", "AA15"], ["AF10", "AF15", "AK15"],
           ["AP10", "AP15", "AU15"], ["AZ10", "AZ15", "BE15"],
           ["BJ10", "BJ15", "BO15"], ["BT10", "BT15", "BY15"],
           ["CD10", "CD15", "CI15"], ["CN10", "CN15", "CS15"],
           ["CX10", "CX15", "DC15"],
           ["DH10", "DH15", "DM15"], ["DR10", "DR15", "DW15"],
           ["EB10", "EB15", "EG15"], ["EL10", "EL15", "EQ15"],
           ["EV10", "EV15", "FA15"],
           ["FF10", "FF15", "FK15"], ["FP10", "FP15", "FU15"],
           ["FZ10", "FZ15", "GE15"], ["GJ10", "GJ15", "GO15"],
           ["GT10", "GT15", "GY15"],
           ["HD10", "HD15", "HI15"], ["HN10", "HN15", "HS15"],
           ["HX10", "HX15", "IC15"], ["IH10", "IH15", "IM15"],
           ["IR10", "IR15", "IW15"],
           ["JB10", "JB15", "JG15"], ["JL10", "JL15", "JQ15"],
           ["JV10", "JV15", "KA15"], ["KF10", "KF15", "KK15"],
           ["KP10", "KP15", "KU15"],
           ["KZ10", "KZ15", "LE15"], ["LJ10", "LJ15", "LO15"],
           ["LT10", "LT15", "LY15"], ["MD10", "MD15", "MI15"],
           ["MN10", "MN15", "MS15"],
           ["MX10", "MX15", "NC15"], ["NH10", "NH15", "NM15"],
           ["NR10", "NR15", "NW15"], ["OB10", "OB15", "OG15"],
           ["OL10", "OL15", "OQ15"],
           ["OV10", "OV15", "PA15"], ["PF10", "PF15", "PK15"],
           ["PP10", "PP15", "PU15"], ["PZ10", "PZ15", "QE15"],
           ["QJ10", "QJ15", "QO15"],
           ["QT10", "QT15", "QY15"], ["RD10", "RD15", "RI15"],
           ["RN10", "RN15", "RS15"], ["RX10", "RX15", "SC15"],
           ["SH10", "SH15", "SM15"],
           ["SR10", "SR15", "SW15"], ["TB10", "TB15", "TG15"],
           ["TL10", "TL15", "TQ15"], ["TV10", "TV15", "UA15"],
           ["UF10", "UF15", "UK15"],
           ["UP10", "UP15", "UU15"], ["UZ10", "UZ15", "VE15"],
           ["VJ10", "VJ15", "VO15"], ["VT10", "VT15", "VY15"],
           ["WD10", "WD15", "WI15"],
           ["WN10", "WN15", "WS15"], ["WX10", "WX15", "XC15"],
           ["XH10", "XH15", "XM15"], ["XR10", "XR15", "XW15"],
           ["YB10", "YB15", "YG15"],
           ["YL10", "YL15", "YQ15"], ["YV10", "YV15", "ZA15"],
           ["ZF10", "ZF15", "ZK15"], ["ZP10", "ZP15", "ZU15"],
           ["ZZ10", "ZZ15", "AAE15"], ["AAJ10", "AAJ15", "AAO15"],
           ["AAT10", "AAT15", "AAY15"], ["ABD10", "ABD15", "ABI15"],
           ['ABN10', 'ABN15', 'ABS15'], ['ABX10', 'ABX15', 'ACC15'],
           ['ACH10', 'ACH15', 'ACM15'],
           ['ACR10', 'ACR15', 'ACW10'], ['ADB10', 'ADB15', 'ADG15'],
           ['ADL10', 'ADL15', 'ADQ15'], ['ADV10', 'ADV15', 'AEA15'],
           ['AEF10', 'AEF15', 'AEK15'], ['AEP10', 'AEP15', 'AEU15'],
           ['AEZ10', 'AEZ15', 'AFE15'], ['AFJ10', 'AFJ15', 'AFO15'],
           ['AFT10', 'AFT15', 'AFY15'], ['AGD10', 'AGD15', 'AGI15'],
           ['AGN10', 'AGN15', 'AGS15'], ['AGX10', 'AGX15', 'AHC15'],
           ['AHH10', 'AHH15', 'AHM15'], ['AHR10', 'AHR15', 'AHW15'],
           ['AIB10', 'AIB15', 'AIG15'], ['AIL10', 'AIL15', 'AIQ15'],
           ['AIV10', 'AIV15', 'AJA15'], ['AJF10', 'AJF15', 'AJK15'],
           ['AJP10', 'AJP15', 'AJU15'], ['AJZ10', 'AJZ15', 'AKE15'],
           ['AKJ10', 'AKJ15', 'AKO15'], ['AKT10', 'AKT15', 'AKY15'],
           ['ALD10', 'ALD15', 'ALI15'], ['ALN10', 'ALN15', 'ALS15'],
           ['ALX10', 'ALX15', 'AMC15'], ['AMH10', 'AMH15', 'AMM15'],
           ['AMR10', 'AMR15', 'AMW15'], ['ANB10', 'ANB15', 'ANG15'],
           ['ANL10', 'ANL15', 'ANG15']]

pic_2_2 = [["V10", "AA10"], ["AF10", "AK10"], ["AP10", "AU10"],
           ["AZ10", "BE10"],
           ["BJ10", "BO10"], ["BT10", "BY10"], ["CD10", "CI10"],
           ["CN10", "CS10"], ["CX10", "DC10"],
           ["DH10", "DM10"], ["DR10", "DW10"], ["EB10", "EG10"],
           ["EL10", "EQ10"], ["EV10", "FA10"],
           ["FF10", "FK10"], ["FP10", "FU10"], ["FZ10", "GE10"],
           ["GJ10", "GO10"], ["GT10", "GY10"],
           ["HD10", "HI10"], ["HN10", "HS10"], ["HX10", "IC10"],
           ["IH10", "IM10"], ["IR10", "IW10"],
           ["JB10", "JG10"], ["JL10", "JQ10"], ["JV10", "KA10"],
           ["KF10", "KK10"], ["KP10", "KU10"],
           ["KZ10", "LE10"], ["LJ10", "LO10"], ["LT10", "LY10"],
           ["MD10", "MI10"], ["MN10", "MS10"],
           ["MX10", "NC10"], ["NH10", "NM10"], ["NR10", "NW10"],
           ["OB10", "OG10"], ["OL10", "OQ10"],
           ["OV10", "PA10"], ["PF10", "PK10"], ["PP10", "PU10"],
           ["PZ10", "QE10"], ["QJ10", "QO10"],
           ["QT10", "QY10"], ["RD10", "RI10"], ["RN10", "RS10"],
           ["RX10", "SC10"], ["SH10", "SM10"],
           ["SR10", "SW10"], ["TB10", "TG10"], ["TL10", "TQ10"],
           ["TV10", "UA10"], ["UF10", "UK10"],
           ["UP10", "UU10"], ["UZ10", "VE10"], ["VJ10", "VO10"],
           ["VT10", "VY10"], ["WD10", "WI10"],
           ["WN10", "WS10"], ["WX10", "XC10"], ["XH10", "XM10"],
           ["XR10", "XW10"], ["YB10", "YG10"],
           ["YL10", "YQ10"], ["YV10", "ZA10"], ["ZF10", "ZK10"],
           ["ZP10", "ZU10"], ["ZZ10", "AAE10"], ["AAJ10", "AAO10"],
           ["AAT10", "AAY10"], ["ABD10", "ABI10"],
           ['ABN10', 'ABS10'], ['ABX10', 'ACC10'],
           ['ACH10', 'ACM10'],
           ['ACR10', 'ACW10'], ['ADB10', 'ADG10'],
           ['ADL10', 'ADQ10'], ['ADV10', 'AEA10'],
           ['AEF10', 'AEK10'], ['AEP10', 'AEU10'],
           ['AEZ10', 'AFE10'], ['AFJ10', 'AFO10'],
           ['AFT10', 'AFY10'], ['AGD10', 'AGI10'],
           ['AGN10', 'AGS10'], ['AGX10', 'AHC10'],
           ['AHH10', 'AHM10'], ['AHR10', 'AHW10'],
           ['AIB10', 'AIG10'], ['AIL10', 'AIQ10'],
           ['AIV10', 'AJA10'], ['AJF10', 'AJK10'],
           ['AJP10', 'AJU10'], ['AJZ10', 'AKE10'],
           ['AKJ10', 'AKO10'], ['AKT10', 'AKY10'],
           ['ALD10', 'ALI10'], ['ALN10', 'ALS10'],
           ['ALX10', 'AMC10'], ['AMH10', 'AMM10'],
           ['AMR10', 'AMW10'], ['ANB10', 'ANG10']]

pic_2_2_merged = [["V15", "AA15"], ["AF15", "AK15"], ["AP15", "AU15"],
                  ["AZ15", "BE15"],
                  ["BJ15", "BO15"], ["BT15", "BY15"], ["CD15", "CI15"],
                  ["CN15", "CS15"], ["CX15", "DC15"],
                  ["DH15", "DM15"], ["DR15", "DW15"], ["EB15", "EG15"],
                  ["EL15", "EQ15"], ["EV15", "FA15"],
                  ["FF15", "FK15"], ["FP15", "FU15"], ["FZ15", "GE15"],
                  ["GJ15", "GO15"], ["GT15", "GY15"],
                  ["HD15", "HI15"], ["HN15", "HS15"], ["HX15", "IC15"],
                  ["IH15", "IM15"], ["IR15", "IW15"],
                  ["JB15", "JG15"], ["JL15", "JQ15"], ["JV15", "KA15"],
                  ["KF15", "KK15"], ["KP15", "KU15"],
                  ["KZ15", "LE15"], ["LJ15", "LO15"], ["LT15", "LY15"],
                  ["MD15", "MI15"], ["MN15", "MS15"],
                  ["MX15", "NC15"], ["NH15", "NM15"], ["NR15", "NW15"],
                  ["OB15", "OG15"], ["OL15", "OQ15"],
                  ["OV15", "PA15"], ["PF15", "PK15"], ["PP15", "PU15"],
                  ["PZ15", "QE15"], ["QJ15", "QO15"],
                  ["QT15", "QY15"], ["RD15", "RI15"], ["RN15", "RS15"],
                  ["RX15", "SC15"], ["SH15", "SM15"],
                  ["SR15", "SW15"], ["TB15", "TG15"], ["TL15", "TQ15"],
                  ["TV15", "UA15"], ["UF15", "UK15"],
                  ["UP15", "UU15"], ["UZ15", "VE15"], ["VJ15", "VO15"],
                  ["VT15", "VY15"], ["WD15", "WI15"],
                  ["WN15", "WS15"], ["WX15", "XC15"], ["XH15", "XM15"],
                  ["XR15", "XW15"], ["YB15", "YG15"],
                  ["YL15", "YQ15"], ["YV15", "ZA15"], ["ZF15", "ZK15"],
                  ["ZP15", "ZU15"], ["ZZ15", "AAE15"], ["AAJ15", "AAO15"],
                  ["AAT15", "AAY15"], ["ABD15", "ABI15"],
                  ['ABN15', 'ABS15'], ['ABX15', 'ACC15'],
                  ['ACH15', 'ACM15'],
                  ['ACR15', 'ACW15'], ['ADB15', 'ADG15'],
                  ['ADL15', 'ADQ15'], ['ADV15', 'AEA15'],
                  ['AEF15', 'AEK15'], ['AEP15', 'AEU15'],
                  ['AEZ15', 'AFE15'], ['AFJ15', 'AFO15'],
                  ['AFT15', 'AFY15'], ['AGD15', 'AGI15'],
                  ['AGN15', 'AGS15'], ['AGX15', 'AHC15'],
                  ['AHH15', 'AHM15'], ['AHR15', 'AHW15'],
                  ['AIB15', 'AIG15'], ['AIL15', 'AIQ15'],
                  ['AIV15', 'AJA15'], ['AJF15', 'AJK15'],
                  ['AJP15', 'AJU15'], ['AJZ15', 'AKE15'],
                  ['AKJ15', 'AKO15'], ['AKT15', 'AKY15'],
                  ['ALD15', 'ALI15'], ['ALN15', 'ALS15'],
                  ['ALX15', 'AMC15'], ['AMH15', 'AMM15'],
                  ['AMR15', 'AMW15']]

pic_1_2 = [["AA10", "AA15"], ["AK10", "AK15"], ["AU10", "AU15"],
           ["BE10", "BE15"],
           ["BO10", "BO15"], ["BY10", "BY15"], ["CI10", "CI15"],
           ["CS10", "CS15"], ["DC10", "DC15"],
           ["DM10", "DM15"], ["DW10", "DW15"], ["EG10", "EG15"],
           ["EQ10", "EQ15"], ["FA10", "FA15"],
           ["FK10", "FK15"], ["FU10", "FU15"], ["GE10", "GE15"],
           ["GO10", "GO15"], ["GY10", "GY15"],
           ["HI10", "HI15"], ["HS10", "HS15"], ["IC10", "IC15"],
           ["IM10", "IM15"], ["IW10", "IW15"],
           ["JG10", "JG15"], ["JQ10", "JQ15"], ["KA10", "KA15"],
           ["KK10", "KK15"], ["KU10", "KU15"],
           ["LE10", "LE15"], ["LO10", "LO15"], ["LY10", "LY15"],
           ["MI10", "MI15"], ["MS10", "MS15"],
           ["NC10", "NC15"], ["NM10", "NM15"], ["NW10", "NW15"],
           ["OG10", "OG15"], ["OQ10", "OQ15"],
           ["PA10", "PA15"], ["PK10", "PK15"], ["PU10", "PU15"],
           ["QE10", "QE15"], ["QO10", "QO15"],
           ["QY10", "QY15"], ["RI10", "RI15"], ["RS10", "RS15"],
           ["SC10", "SC15"], ["SM10", "SM15"],
           ["SW10", "SW15"], ["TG10", "TG15"], ["TQ10", "TQ15"],
           ["UA10", "UA15"], ["UK10", "UK15"],
           ["UU10", "UU15"], ["VE10", "VE15"], ["VO10", "VO15"],
           ["VY10", "VY15"], ["WI10", "WI15"],
           ["WS10", "WS15"], ["XC10", "XC15"], ["XM10", "XM15"],
           ["XW10", "XW15"], ["YG10", "YG15"],
           ["YQ10", "YQ15"], ["ZA10", "ZA15"], ["ZK10", "ZK15"],
           ["ZU10", "ZU15"], ["AAE10", "AAE15"], ["AAO10", "AAO15"],
           ["AAY10", "AAY15"], ["ABI10", "ABI15"],
           ['ABS10', 'ABS15'], ['ACC10', 'ACC15'],
           ['ACM10', 'ACM15'],
           ['ACW10', 'ACW15'], ['ADG10', 'ADG15'],
           ['ADQ10', 'ADQ15'], ['AEA10', 'AEA15'],
           ['AEK10', 'AEK15'], ['AEU10', 'AEU15'],
           ['AFE10', 'AFE15'], ['AFO10', 'AFO15'],
           ['AFY10', 'AFY15'], ['AGI10', 'AGI15'],
           ['AGS10', 'AGS15'], ['AHC10', 'AHC15'],
           ['AHM10', 'AHM15'], ['AHW10', 'AHW15'],
           ['AIG10', 'AIG15'], ['AIQ10', 'AIQ15'],
           ['AJA10', 'AJA15'], ['AJK10', 'AJK15'],
           ['AJU10', 'AJU15'], ['AKE10', 'AKE15'],
           ['AKO10', 'AKO15'], ['AKY10', 'AKY15'],
           ['ALI10', 'ALI15'], ['ALS10', 'ALS15'],
           ['AMC10', 'AMC15'], ['AMM10', 'AMM15'],
           ['AMW10', 'AMW15'], ['ANG10', 'ANG15']]

pic_4_3 = [["AF10", "AK10", "AF15", "AK15"], ["AP10", "AU10", "AP15", "AU15"],
           ["AZ10", "BE10", "AZ15", "BE15"],
           ["BJ10", "BO10", "BJ15", "BO15"], ["BT10", "BY10", "BT15", "BY15"],
           ["CD10", "CI10", "CD15", "CI15"], ["CN10", "CS10", "CN15", "CS15"],
           ["CX10", "DC10", "CX15", "DC15"],
           ["DH10", "DM10", "DH15", "DM15"], ["DR10", "DW10", "DR15", "DW15"],
           ["EB10", "EG10", "EB15", "EG15"], ["EL10", "EQ10", "EL15", "EQ15"],
           ["EV10", "FA10", "EV15", "FA15"],
           ["FF10", "FK10", "FF15", "FK15"], ["FP10", "FU10", "FP15", "FU15"],
           ["FZ10", "GE10", "FZ15", "GE15"], ["GJ10", "GO10", "GJ15", "GO15"],
           ["GT10", "GY10", "GT15", "GY15"],
           ["HD10", "HI10", "HD15", "HI15"], ["HN10", "HS10", "HN15", "HS15"],
           ["HX10", "IC10", "HX15", "IC15"], ["IH10", "IM10", "IH15", "IM15"],
           ["IR10", "IW10", "IR15", "IW15"],
           ["JB10", "JG10", "JB15", "JG15"], ["JL10", "JQ10", "JL15", "JQ15"],
           ["JV10", "KA10", "JV15", "KA15"], ["KF10", "KK10", "KF15", "KK15"],
           ["KP10", "KU10", "KP15", "KU15"],
           ["KZ10", "LE10", "KZ15", "LE15"], ["LJ10", "LO10", "LJ15", "LO15"],
           ["LT10", "LY10", "LT15", "LY15"], ["MD10", "MI10", "MD15", "MI15"],
           ["MN10", "MS10", "MN15", "MS15"],
           ["MX10", "NC10", "MX15", "NC15"], ["NH10", "NM10", "NH15", "NM15"],
           ["NR10", "NW10", "NR15", "NW15"], ["OB10", "OG10", "OB15", "OG15"],
           ["OL10", "OQ10", "OL15", "OQ15"],
           ["OV10", "PA10", "OV15", "PA15"], ["PF10", "PK10", "PF15", "PK15"],
           ["PP10", "PU10", "PP15", "PU15"], ["PZ10", "QE10", "PZ15", "QE15"],
           ["QJ10", "QO10", "QJ15", "QO15"],
           ["QT10", "QY10", "QT15", "QY15"], ["RD10", "RI10", "RD15", "RI15"],
           ["RN10", "RS10", "RN15", "RS15"], ["RX10", "SC10", "RX15", "SC15"],
           ["SH10", "SM10", "SH15", "SM15"],
           ["SR10", "SW10", "SR15", "SW15"], ["TB10", "TG10", "TB15", "TG15"],
           ["TL10", "TQ10", "TL15", "TQ15"], ["TV10", "UA10", "TV15", "UA15"],
           ["UF10", "UK10", "UF15", "UK15"],
           ["UP10", "UU10", "UP15", "UU15"], ["UZ10", "VE10", "UZ15", "VE15"],
           ["VJ10", "VO10", "VJ15", "VO15"], ["VT10", "VY10", "VT15", "VY15"],
           ["WD10", "WI10", "WD15", "WI15"],
           ["WN10", "WS10", "WN15", "WS15"], ["WX10", "XC10", "WX15", "XC15"],
           ["XH10", "XM10", "XH15", "XM15"], ["XR10", "XW10", "XR15", "XW15"],
           ["YB10", "YG10", "YB15", "YG15"],
           ["YL10", "YQ10", "YL15", "YQ15"], ["YV10", "ZA10", "YV15", "ZA15"],
           ["ZF10", "ZK10", "ZF15", "ZK15"], ["ZP10", "ZU10", "ZP15", "ZU15"],
           ["ZZ10", "AAE10", "ZZ15", "AAE15"],
           ["AAJ10", "AAO10", "AAJ15", "AAO15"],
           ["AAT10", "AAY10", "AAT15", "AAY15"],
           ["ABD10", "ABI10", "ABD15", "ABI15"],
           ['ABN10', 'ABS10', 'ABN15', 'ABS15'],
           ['ABX10', 'ACC10', 'ABX15', 'ACC15'],
           ['ACH10', 'ACM10', 'ACH15', 'ACM15'],
           ['ACR10', 'ACW10', 'ACR15', 'ACW10'],
           ['ADB10', 'ADG10', 'ADB15', 'ADG15'],
           ['ADL10', 'ADQ10', 'ADL15', 'ADQ15'],
           ['ADV10', 'AEA10', 'ADV15', 'AEA15'],
           ['AEF10', 'AEK10', 'AEF15', 'AEK15'],
           ['AEP10', 'AEU10', 'AEP15', 'AEU15'],
           ['AEZ10', 'AFE10', 'AEZ15', 'AFE15'],
           ['AFJ10', 'AFO10', 'AFJ15', 'AFO15'],
           ['AFT10', 'AFY10', 'AFT15', 'AFY15'],
           ['AGD10', 'AGI10', 'AGD15', 'AGI15'],
           ['AGN10', 'AGS10', 'AGN15', 'AGS15'],
           ['AGX10', 'AHC10', 'AGX15', 'AHC15'],
           ['AHH10', 'AHM10', 'AHH15', 'AHM15'],
           ['AHR10', 'AHW10', 'AHR15', 'AHW15'],
           ['AIB10', 'AIG10', 'AIB15', 'AIG15'],
           ['AIL10', 'AIQ10', 'AIL15', 'AIQ15'],
           ['AIV10', 'AJA10', 'AIV15', 'AJA15'],
           ['AJF10', 'AJK10', 'AJF15', 'AJK15'],
           ['AJP10', 'AJU10', 'AJP15', 'AJU15'],
           ['AJZ10', 'AKE10', 'AJZ15', 'AKE15'],
           ['AKJ10', 'AKO10', 'AKJ15', 'AKO15'],
           ['AKT10', 'AKY10', 'AKT15', 'AKY15'],
           ['ALD10', 'ALI10', 'ALD15', 'ALI15'],
           ['ALN10', 'ALS10', 'ALN15', 'ALS15'],
           ['ALX10', 'AMC10', 'ALX15', 'AMC15'],
           ['AMH10', 'AMM10', 'AMH15', 'AMM15'],
           ['AMR10', 'AMW10', 'AMR15', 'AMW15'],
           ['ANB10', 'ANG10', 'ANB15', 'ANG15']]

pic_3_3 = [["AF10", "AF15", "AK15"], ["AP10", "AP15", "AU15"],
           ["AZ10", "AZ15", "BE15"],
           ["BJ10", "BJ15", "BO15"], ["BT10", "BT15", "BY15"],
           ["CD10", "CD15", "CI15"], ["CN10", "CN15", "CS15"],
           ["CX10", "CX15", "DC15"],
           ["DH10", "DH15", "DM15"], ["DR10", "DR15", "DW15"],
           ["EB10", "EB15", "EG15"], ["EL10", "EL15", "EQ15"],
           ["EV10", "EV15", "FA15"],
           ["FF10", "FF15", "FK15"], ["FP10", "FP15", "FU15"],
           ["FZ10", "FZ15", "GE15"], ["GJ10", "GJ15", "GO15"],
           ["GT10", "GT15", "GY15"],
           ["HD10", "HD15", "HI15"], ["HN10", "HN15", "HS15"],
           ["HX10", "HX15", "IC15"], ["IH10", "IH15", "IM15"],
           ["IR10", "IR15", "IW15"],
           ["JB10", "JB15", "JG15"], ["JL10", "JL15", "JQ15"],
           ["JV10", "JV15", "KA15"], ["KF10", "KF15", "KK15"],
           ["KP10", "KP15", "KU15"],
           ["KZ10", "KZ15", "LE15"], ["LJ10", "LJ15", "LO15"],
           ["LT10", "LT15", "LY15"], ["MD10", "MD15", "MI15"],
           ["MN10", "MN15", "MS15"],
           ["MX10", "MX15", "NC15"], ["NH10", "NH15", "NM15"],
           ["NR10", "NR15", "NW15"], ["OB10", "OB15", "OG15"],
           ["OL10", "OL15", "OQ15"],
           ["OV10", "OV15", "PA15"], ["PF10", "PF15", "PK15"],
           ["PP10", "PP15", "PU15"], ["PZ10", "PZ15", "QE15"],
           ["QJ10", "QJ15", "QO15"],
           ["QT10", "QT15", "QY15"], ["RD10", "RD15", "RI15"],
           ["RN10", "RN15", "RS15"], ["RX10", "RX15", "SC15"],
           ["SH10", "SH15", "SM15"],
           ["SR10", "SR15", "SW15"], ["TB10", "TB15", "TG15"],
           ["TL10", "TL15", "TQ15"], ["TV10", "TV15", "UA15"],
           ["UF10", "UF15", "UK15"],
           ["UP10", "UP15", "UU15"], ["UZ10", "UZ15", "VE15"],
           ["VJ10", "VJ15", "VO15"], ["VT10", "VT15", "VY15"],
           ["WD10", "WD15", "WI15"],
           ["WN10", "WN15", "WS15"], ["WX10", "WX15", "XC15"],
           ["XH10", "XH15", "XM15"], ["XR10", "XR15", "XW15"],
           ["YB10", "YB15", "YG15"],
           ["YL10", "YL15", "YQ15"], ["YV10", "YV15", "ZA15"],
           ["ZF10", "ZF15", "ZK15"], ["ZP10", "ZP15", "ZU15"],
           ["ZZ10", "ZZ15", "AAE15"], ["AAJ10", "AAJ15", "AAO15"],
           ["AAT10", "AAT15", "AAY15"], ["ABD10", "ABD15", "ABI15"],
           ['ABN10', 'ABN15', 'ABS15'], ['ABX10', 'ABX15', 'ACC15'],
           ['ACH10', 'ACH15', 'ACM15'],
           ['ACR10', 'ACR15', 'ACW10'], ['ADB10', 'ADB15', 'ADG15'],
           ['ADL10', 'ADL15', 'ADQ15'], ['ADV10', 'ADV15', 'AEA15'],
           ['AEF10', 'AEF15', 'AEK15'], ['AEP10', 'AEP15', 'AEU15'],
           ['AEZ10', 'AEZ15', 'AFE15'], ['AFJ10', 'AFJ15', 'AFO15'],
           ['AFT10', 'AFT15', 'AFY15'], ['AGD10', 'AGD15', 'AGI15'],
           ['AGN10', 'AGN15', 'AGS15'], ['AGX10', 'AGX15', 'AHC15'],
           ['AHH10', 'AHH15', 'AHM15'], ['AHR10', 'AHR15', 'AHW15'],
           ['AIB10', 'AIB15', 'AIG15'], ['AIL10', 'AIL15', 'AIQ15'],
           ['AIV10', 'AIV15', 'AJA15'], ['AJF10', 'AJF15', 'AJK15'],
           ['AJP10', 'AJP15', 'AJU15'], ['AJZ10', 'AJZ15', 'AKE15'],
           ['AKJ10', 'AKJ15', 'AKO15'], ['AKT10', 'AKT15', 'AKY15'],
           ['ALD10', 'ALD15', 'ALI15'], ['ALN10', 'ALN15', 'ALS15'],
           ['ALX10', 'ALX15', 'AMC15'], ['AMH10', 'AMH15', 'AMM15'],
           ['AMR10', 'AMR15', 'AMW15'], ['ANB10', 'ANB15', 'ANG15'],
           ['ANL10', 'ANL15', 'ANG15']]

pic_2_3 = [["AF10", "AK10"], ["AP10", "AU10"], ["AZ10", "BE10"],
           ["BJ10", "BO10"], ["BT10", "BY10"], ["CD10", "CI10"],
           ["CN10", "CS10"], ["CX10", "DC10"],
           ["DH10", "DM10"], ["DR10", "DW10"], ["EB10", "EG10"],
           ["EL10", "EQ10"], ["EV10", "FA10"],
           ["FF10", "FK10"], ["FP10", "FU10"], ["FZ10", "GE10"],
           ["GJ10", "GO10"], ["GT10", "GY10"],
           ["HD10", "HI10"], ["HN10", "HS10"], ["HX10", "IC10"],
           ["IH10", "IM10"], ["IR10", "IW10"],
           ["JB10", "JG10"], ["JL10", "JQ10"], ["JV10", "KA10"],
           ["KF10", "KK10"], ["KP10", "KU10"],
           ["KZ10", "LE10"], ["LJ10", "LO10"], ["LT10", "LY10"],
           ["MD10", "MI10"], ["MN10", "MS10"],
           ["MX10", "NC10"], ["NH10", "NM10"], ["NR10", "NW10"],
           ["OB10", "OG10"], ["OL10", "OQ10"],
           ["OV10", "PA10"], ["PF10", "PK10"], ["PP10", "PU10"],
           ["PZ10", "QE10"], ["QJ10", "QO10"],
           ["QT10", "QY10"], ["RD10", "RI10"], ["RN10", "RS10"],
           ["RX10", "SC10"], ["SH10", "SM10"],
           ["SR10", "SW10"], ["TB10", "TG10"], ["TL10", "TQ10"],
           ["TV10", "UA10"], ["UF10", "UK10"],
           ["UP10", "UU10"], ["UZ10", "VE10"], ["VJ10", "VO10"],
           ["VT10", "VY10"], ["WD10", "WI10"],
           ["WN10", "WS10"], ["WX10", "XC10"], ["XH10", "XM10"],
           ["XR10", "XW10"], ["YB10", "YG10"],
           ["YL10", "YQ10"], ["YV10", "ZA10"], ["ZF10", "ZK10"],
           ["ZP10", "ZU10"], ["ZZ10", "AAE10"], ["AAJ10", "AAO10"],
           ["AAT10", "AAY10"], ["ABD10", "ABI10"],
           ['ABN10', 'ABS10'], ['ABX10', 'ACC10'],
           ['ACH10', 'ACM10'],
           ['ACR10', 'ACW10'], ['ADB10', 'ADG10'],
           ['ADL10', 'ADQ10'], ['ADV10', 'AEA10'],
           ['AEF10', 'AEK10'], ['AEP10', 'AEU10'],
           ['AEZ10', 'AFE10'], ['AFJ10', 'AFO10'],
           ['AFT10', 'AFY10'], ['AGD10', 'AGI10'],
           ['AGN10', 'AGS10'], ['AGX10', 'AHC10'],
           ['AHH10', 'AHM10'], ['AHR10', 'AHW10'],
           ['AIB10', 'AIG10'], ['AIL10', 'AIQ10'],
           ['AIV10', 'AJA10'], ['AJF10', 'AJK10'],
           ['AJP10', 'AJU10'], ['AJZ10', 'AKE10'],
           ['AKJ10', 'AKO10'], ['AKT10', 'AKY10'],
           ['ALD10', 'ALI10'], ['ALN10', 'ALS10'],
           ['ALX10', 'AMC10'], ['AMH10', 'AMM10'],
           ['AMR10', 'AMW10'], ['ANB10', 'ANG10']]

pic_2_3_merged = [["AF15", "AK15"], ["AP15", "AU15"], ["AZ15", "BE15"],
                  ["BJ15", "BO15"], ["BT15", "BY15"], ["CD15", "CI15"],
                  ["CN15", "CS15"], ["CX15", "DC15"],
                  ["DH15", "DM15"], ["DR15", "DW15"], ["EB15", "EG15"],
                  ["EL15", "EQ15"], ["EV15", "FA15"],
                  ["FF15", "FK15"], ["FP15", "FU15"], ["FZ15", "GE15"],
                  ["GJ15", "GO15"], ["GT15", "GY15"],
                  ["HD15", "HI15"], ["HN15", "HS15"], ["HX15", "IC15"],
                  ["IH15", "IM15"], ["IR15", "IW15"],
                  ["JB15", "JG15"], ["JL15", "JQ15"], ["JV15", "KA15"],
                  ["KF15", "KK15"], ["KP15", "KU15"],
                  ["KZ15", "LE15"], ["LJ15", "LO15"], ["LT15", "LY15"],
                  ["MD15", "MI15"], ["MN15", "MS15"],
                  ["MX15", "NC15"], ["NH15", "NM15"], ["NR15", "NW15"],
                  ["OB15", "OG15"], ["OL15", "OQ15"],
                  ["OV15", "PA15"], ["PF15", "PK15"], ["PP15", "PU15"],
                  ["PZ15", "QE15"], ["QJ15", "QO15"],
                  ["QT15", "QY15"], ["RD15", "RI15"], ["RN15", "RS15"],
                  ["RX15", "SC15"], ["SH15", "SM15"],
                  ["SR15", "SW15"], ["TB15", "TG15"], ["TL15", "TQ15"],
                  ["TV15", "UA15"], ["UF15", "UK15"],
                  ["UP15", "UU15"], ["UZ15", "VE15"], ["VJ15", "VO15"],
                  ["VT15", "VY15"], ["WD15", "WI15"],
                  ["WN15", "WS15"], ["WX15", "XC15"], ["XH15", "XM15"],
                  ["XR15", "XW15"], ["YB15", "YG15"],
                  ["YL15", "YQ15"], ["YV15", "ZA15"], ["ZF15", "ZK15"],
                  ["ZP15", "ZU15"], ["ZZ15", "AAE15"], ["AAJ15", "AAO15"],
                  ["AAT15", "AAY15"], ["ABD15", "ABI15"],
                  ['ABN15', 'ABS15'], ['ABX15', 'ACC15'],
                  ['ACH15', 'ACM15'],
                  ['ACR15', 'ACW15'], ['ADB15', 'ADG15'],
                  ['ADL15', 'ADQ15'], ['ADV15', 'AEA15'],
                  ['AEF15', 'AEK15'], ['AEP15', 'AEU15'],
                  ['AEZ15', 'AFE15'], ['AFJ15', 'AFO15'],
                  ['AFT15', 'AFY15'], ['AGD15', 'AGI15'],
                  ['AGN15', 'AGS15'], ['AGX15', 'AHC15'],
                  ['AHH15', 'AHM15'], ['AHR15', 'AHW15'],
                  ['AIB15', 'AIG15'], ['AIL15', 'AIQ15'],
                  ['AIV15', 'AJA15'], ['AJF15', 'AJK15'],
                  ['AJP15', 'AJU15'], ['AJZ15', 'AKE15'],
                  ['AKJ15', 'AKO15'], ['AKT15', 'AKY15'],
                  ['ALD15', 'ALI15'], ['ALN15', 'ALS15'],
                  ['ALX15', 'AMC15'], ['AMH15', 'AMM15'],
                  ['AMR15', 'AMW15']]

pic_1_3 = [["AK10", "AK15"], ["AU10", "AU15"], ["BE10", "BE15"],
           ["BO10", "BO15"], ["BY10", "BY15"], ["CI10", "CI15"],
           ["CS10", "CS15"], ["DC10", "DC15"],
           ["DM10", "DM15"], ["DW10", "DW15"], ["EG10", "EG15"],
           ["EQ10", "EQ15"], ["FA10", "FA15"],
           ["FK10", "FK15"], ["FU10", "FU15"], ["GE10", "GE15"],
           ["GO10", "GO15"], ["GY10", "GY15"],
           ["HI10", "HI15"], ["HS10", "HS15"], ["IC10", "IC15"],
           ["IM10", "IM15"], ["IW10", "IW15"],
           ["JG10", "JG15"], ["JQ10", "JQ15"], ["KA10", "KA15"],
           ["KK10", "KK15"], ["KU10", "KU15"],
           ["LE10", "LE15"], ["LO10", "LO15"], ["LY10", "LY15"],
           ["MI10", "MI15"], ["MS10", "MS15"],
           ["NC10", "NC15"], ["NM10", "NM15"], ["NW10", "NW15"],
           ["OG10", "OG15"], ["OQ10", "OQ15"],
           ["PA10", "PA15"], ["PK10", "PK15"], ["PU10", "PU15"],
           ["QE10", "QE15"], ["QO10", "QO15"],
           ["QY10", "QY15"], ["RI10", "RI15"], ["RS10", "RS15"],
           ["SC10", "SC15"], ["SM10", "SM15"],
           ["SW10", "SW15"], ["TG10", "TG15"], ["TQ10", "TQ15"],
           ["UA10", "UA15"], ["UK10", "UK15"],
           ["UU10", "UU15"], ["VE10", "VE15"], ["VO10", "VO15"],
           ["VY10", "VY15"], ["WI10", "WI15"],
           ["WS10", "WS15"], ["XC10", "XC15"], ["XM10", "XM15"],
           ["XW10", "XW15"], ["YG10", "YG15"],
           ["YQ10", "YQ15"], ["ZA10", "ZA15"], ["ZK10", "ZK15"],
           ["ZU10", "ZU15"], ["AAE10", "AAE15"], ["AAO10", "AAO15"],
           ["AAY10", "AAY15"], ["ABI10", "ABI15"],
           ['ABS10', 'ABS15'], ['ACC10', 'ACC15'],
           ['ACM10', 'ACM15'],
           ['ACW10', 'ACW15'], ['ADG10', 'ADG15'],
           ['ADQ10', 'ADQ15'], ['AEA10', 'AEA15'],
           ['AEK10', 'AEK15'], ['AEU10', 'AEU15'],
           ['AFE10', 'AFE15'], ['AFO10', 'AFO15'],
           ['AFY10', 'AFY15'], ['AGI10', 'AGI15'],
           ['AGS10', 'AGS15'], ['AHC10', 'AHC15'],
           ['AHM10', 'AHM15'], ['AHW10', 'AHW15'],
           ['AIG10', 'AIG15'], ['AIQ10', 'AIQ15'],
           ['AJA10', 'AJA15'], ['AJK10', 'AJK15'],
           ['AJU10', 'AJU15'], ['AKE10', 'AKE15'],
           ['AKO10', 'AKO15'], ['AKY10', 'AKY15'],
           ['ALI10', 'ALI15'], ['ALS10', 'ALS15'],
           ['AMC10', 'AMC15'], ['AMM10', 'AMM15'],
           ['AMW10', 'AMW15'], ['ANG10', 'ANG15']]

pic_4_4 = [["AP10", "AU10", "AP15", "AU15"], ["AZ10", "BE10", "AZ15", "BE15"],
           ["BJ10", "BO10", "BJ15", "BO15"], ["BT10", "BY10", "BT15", "BY15"],
           ["CD10", "CI10", "CD15", "CI15"], ["CN10", "CS10", "CN15", "CS15"],
           ["CX10", "DC10", "CX15", "DC15"],
           ["DH10", "DM10", "DH15", "DM15"], ["DR10", "DW10", "DR15", "DW15"],
           ["EB10", "EG10", "EB15", "EG15"], ["EL10", "EQ10", "EL15", "EQ15"],
           ["EV10", "FA10", "EV15", "FA15"],
           ["FF10", "FK10", "FF15", "FK15"], ["FP10", "FU10", "FP15", "FU15"],
           ["FZ10", "GE10", "FZ15", "GE15"], ["GJ10", "GO10", "GJ15", "GO15"],
           ["GT10", "GY10", "GT15", "GY15"],
           ["HD10", "HI10", "HD15", "HI15"], ["HN10", "HS10", "HN15", "HS15"],
           ["HX10", "IC10", "HX15", "IC15"], ["IH10", "IM10", "IH15", "IM15"],
           ["IR10", "IW10", "IR15", "IW15"],
           ["JB10", "JG10", "JB15", "JG15"], ["JL10", "JQ10", "JL15", "JQ15"],
           ["JV10", "KA10", "JV15", "KA15"], ["KF10", "KK10", "KF15", "KK15"],
           ["KP10", "KU10", "KP15", "KU15"],
           ["KZ10", "LE10", "KZ15", "LE15"], ["LJ10", "LO10", "LJ15", "LO15"],
           ["LT10", "LY10", "LT15", "LY15"], ["MD10", "MI10", "MD15", "MI15"],
           ["MN10", "MS10", "MN15", "MS15"],
           ["MX10", "NC10", "MX15", "NC15"], ["NH10", "NM10", "NH15", "NM15"],
           ["NR10", "NW10", "NR15", "NW15"], ["OB10", "OG10", "OB15", "OG15"],
           ["OL10", "OQ10", "OL15", "OQ15"],
           ["OV10", "PA10", "OV15", "PA15"], ["PF10", "PK10", "PF15", "PK15"],
           ["PP10", "PU10", "PP15", "PU15"], ["PZ10", "QE10", "PZ15", "QE15"],
           ["QJ10", "QO10", "QJ15", "QO15"],
           ["QT10", "QY10", "QT15", "QY15"], ["RD10", "RI10", "RD15", "RI15"],
           ["RN10", "RS10", "RN15", "RS15"], ["RX10", "SC10", "RX15", "SC15"],
           ["SH10", "SM10", "SH15", "SM15"],
           ["SR10", "SW10", "SR15", "SW15"], ["TB10", "TG10", "TB15", "TG15"],
           ["TL10", "TQ10", "TL15", "TQ15"], ["TV10", "UA10", "TV15", "UA15"],
           ["UF10", "UK10", "UF15", "UK15"],
           ["UP10", "UU10", "UP15", "UU15"], ["UZ10", "VE10", "UZ15", "VE15"],
           ["VJ10", "VO10", "VJ15", "VO15"], ["VT10", "VY10", "VT15", "VY15"],
           ["WD10", "WI10", "WD15", "WI15"],
           ["WN10", "WS10", "WN15", "WS15"], ["WX10", "XC10", "WX15", "XC15"],
           ["XH10", "XM10", "XH15", "XM15"], ["XR10", "XW10", "XR15", "XW15"],
           ["YB10", "YG10", "YB15", "YG15"],
           ["YL10", "YQ10", "YL15", "YQ15"], ["YV10", "ZA10", "YV15", "ZA15"],
           ["ZF10", "ZK10", "ZF15", "ZK15"], ["ZP10", "ZU10", "ZP15", "ZU15"],
           ["ZZ10", "AAE10", "ZZ15", "AAE15"],
           ["AAJ10", "AAO10", "AAJ15", "AAO15"],
           ["AAT10", "AAY10", "AAT15", "AAY15"],
           ["ABD10", "ABI10", "ABD15", "ABI15"],
           ['ABN10', 'ABS10', 'ABN15', 'ABS15'],
           ['ABX10', 'ACC10', 'ABX15', 'ACC15'],
           ['ACH10', 'ACM10', 'ACH15', 'ACM15'],
           ['ACR10', 'ACW10', 'ACR15', 'ACW10'],
           ['ADB10', 'ADG10', 'ADB15', 'ADG15'],
           ['ADL10', 'ADQ10', 'ADL15', 'ADQ15'],
           ['ADV10', 'AEA10', 'ADV15', 'AEA15'],
           ['AEF10', 'AEK10', 'AEF15', 'AEK15'],
           ['AEP10', 'AEU10', 'AEP15', 'AEU15'],
           ['AEZ10', 'AFE10', 'AEZ15', 'AFE15'],
           ['AFJ10', 'AFO10', 'AFJ15', 'AFO15'],
           ['AFT10', 'AFY10', 'AFT15', 'AFY15'],
           ['AGD10', 'AGI10', 'AGD15', 'AGI15'],
           ['AGN10', 'AGS10', 'AGN15', 'AGS15'],
           ['AGX10', 'AHC10', 'AGX15', 'AHC15'],
           ['AHH10', 'AHM10', 'AHH15', 'AHM15'],
           ['AHR10', 'AHW10', 'AHR15', 'AHW15'],
           ['AIB10', 'AIG10', 'AIB15', 'AIG15'],
           ['AIL10', 'AIQ10', 'AIL15', 'AIQ15'],
           ['AIV10', 'AJA10', 'AIV15', 'AJA15'],
           ['AJF10', 'AJK10', 'AJF15', 'AJK15'],
           ['AJP10', 'AJU10', 'AJP15', 'AJU15'],
           ['AJZ10', 'AKE10', 'AJZ15', 'AKE15'],
           ['AKJ10', 'AKO10', 'AKJ15', 'AKO15'],
           ['AKT10', 'AKY10', 'AKT15', 'AKY15'],
           ['ALD10', 'ALI10', 'ALD15', 'ALI15'],
           ['ALN10', 'ALS10', 'ALN15', 'ALS15'],
           ['ALX10', 'AMC10', 'ALX15', 'AMC15'],
           ['AMH10', 'AMM10', 'AMH15', 'AMM15'],
           ['AMR10', 'AMW10', 'AMR15', 'AMW15'],
           ['ANB10', 'ANG10', 'ANB15', 'ANG15']]

pic_3_4 = [["AP10", "AP15", "AU15"], ["AZ10", "AZ15", "BE15"],
           ["BJ10", "BJ15", "BO15"], ["BT10", "BT15", "BY15"],
           ["CD10", "CD15", "CI15"], ["CN10", "CN15", "CS15"],
           ["CX10", "CX15", "DC15"],
           ["DH10", "DH15", "DM15"], ["DR10", "DR15", "DW15"],
           ["EB10", "EB15", "EG15"], ["EL10", "EL15", "EQ15"],
           ["EV10", "EV15", "FA15"],
           ["FF10", "FF15", "FK15"], ["FP10", "FP15", "FU15"],
           ["FZ10", "FZ15", "GE15"], ["GJ10", "GJ15", "GO15"],
           ["GT10", "GT15", "GY15"],
           ["HD10", "HD15", "HI15"], ["HN10", "HN15", "HS15"],
           ["HX10", "HX15", "IC15"], ["IH10", "IH15", "IM15"],
           ["IR10", "IR15", "IW15"],
           ["JB10", "JB15", "JG15"], ["JL10", "JL15", "JQ15"],
           ["JV10", "JV15", "KA15"], ["KF10", "KF15", "KK15"],
           ["KP10", "KP15", "KU15"],
           ["KZ10", "KZ15", "LE15"], ["LJ10", "LJ15", "LO15"],
           ["LT10", "LT15", "LY15"], ["MD10", "MD15", "MI15"],
           ["MN10", "MN15", "MS15"],
           ["MX10", "MX15", "NC15"], ["NH10", "NH15", "NM15"],
           ["NR10", "NR15", "NW15"], ["OB10", "OB15", "OG15"],
           ["OL10", "OL15", "OQ15"],
           ["OV10", "OV15", "PA15"], ["PF10", "PF15", "PK15"],
           ["PP10", "PP15", "PU15"], ["PZ10", "PZ15", "QE15"],
           ["QJ10", "QJ15", "QO15"],
           ["QT10", "QT15", "QY15"], ["RD10", "RD15", "RI15"],
           ["RN10", "RN15", "RS15"], ["RX10", "RX15", "SC15"],
           ["SH10", "SH15", "SM15"],
           ["SR10", "SR15", "SW15"], ["TB10", "TB15", "TG15"],
           ["TL10", "TL15", "TQ15"], ["TV10", "TV15", "UA15"],
           ["UF10", "UF15", "UK15"],
           ["UP10", "UP15", "UU15"], ["UZ10", "UZ15", "VE15"],
           ["VJ10", "VJ15", "VO15"], ["VT10", "VT15", "VY15"],
           ["WD10", "WD15", "WI15"],
           ["WN10", "WN15", "WS15"], ["WX10", "WX15", "XC15"],
           ["XH10", "XH15", "XM15"], ["XR10", "XR15", "XW15"],
           ["YB10", "YB15", "YG15"],
           ["YL10", "YL15", "YQ15"], ["YV10", "YV15", "ZA15"],
           ["ZF10", "ZF15", "ZK15"], ["ZP10", "ZP15", "ZU15"],
           ["ZZ10", "ZZ15", "AAE15"], ["AAJ10", "AAJ15", "AAO15"],
           ["AAT10", "AAT15", "AAY15"], ["ABD10", "ABD15", "ABI15"],
           ['ABN10', 'ABN15', 'ABS15'], ['ABX10', 'ABX15', 'ACC15'],
           ['ACH10', 'ACH15', 'ACM15'],
           ['ACR10', 'ACR15', 'ACW10'], ['ADB10', 'ADB15', 'ADG15'],
           ['ADL10', 'ADL15', 'ADQ15'], ['ADV10', 'ADV15', 'AEA15'],
           ['AEF10', 'AEF15', 'AEK15'], ['AEP10', 'AEP15', 'AEU15'],
           ['AEZ10', 'AEZ15', 'AFE15'], ['AFJ10', 'AFJ15', 'AFO15'],
           ['AFT10', 'AFT15', 'AFY15'], ['AGD10', 'AGD15', 'AGI15'],
           ['AGN10', 'AGN15', 'AGS15'], ['AGX10', 'AGX15', 'AHC15'],
           ['AHH10', 'AHH15', 'AHM15'], ['AHR10', 'AHR15', 'AHW15'],
           ['AIB10', 'AIB15', 'AIG15'], ['AIL10', 'AIL15', 'AIQ15'],
           ['AIV10', 'AIV15', 'AJA15'], ['AJF10', 'AJF15', 'AJK15'],
           ['AJP10', 'AJP15', 'AJU15'], ['AJZ10', 'AJZ15', 'AKE15'],
           ['AKJ10', 'AKJ15', 'AKO15'], ['AKT10', 'AKT15', 'AKY15'],
           ['ALD10', 'ALD15', 'ALI15'], ['ALN10', 'ALN15', 'ALS15'],
           ['ALX10', 'ALX15', 'AMC15'], ['AMH10', 'AMH15', 'AMM15'],
           ['AMR10', 'AMR15', 'AMW15'], ['ANB10', 'ANB15', 'ANG15'],
           ['ANL10', 'ANL15', 'ANG15']]

pic_2_4 = [["AP10", "AU10"], ["AZ10", "BE10"],
           ["BJ10", "BO10"], ["BT10", "BY10"], ["CD10", "CI10"],
           ["CN10", "CS10"], ["CX10", "DC10"],
           ["DH10", "DM10"], ["DR10", "DW10"], ["EB10", "EG10"],
           ["EL10", "EQ10"], ["EV10", "FA10"],
           ["FF10", "FK10"], ["FP10", "FU10"], ["FZ10", "GE10"],
           ["GJ10", "GO10"], ["GT10", "GY10"],
           ["HD10", "HI10"], ["HN10", "HS10"], ["HX10", "IC10"],
           ["IH10", "IM10"], ["IR10", "IW10"],
           ["JB10", "JG10"], ["JL10", "JQ10"], ["JV10", "KA10"],
           ["KF10", "KK10"], ["KP10", "KU10"],
           ["KZ10", "LE10"], ["LJ10", "LO10"], ["LT10", "LY10"],
           ["MD10", "MI10"], ["MN10", "MS10"],
           ["MX10", "NC10"], ["NH10", "NM10"], ["NR10", "NW10"],
           ["OB10", "OG10"], ["OL10", "OQ10"],
           ["OV10", "PA10"], ["PF10", "PK10"], ["PP10", "PU10"],
           ["PZ10", "QE10"], ["QJ10", "QO10"],
           ["QT10", "QY10"], ["RD10", "RI10"], ["RN10", "RS10"],
           ["RX10", "SC10"], ["SH10", "SM10"],
           ["SR10", "SW10"], ["TB10", "TG10"], ["TL10", "TQ10"],
           ["TV10", "UA10"], ["UF10", "UK10"],
           ["UP10", "UU10"], ["UZ10", "VE10"], ["VJ10", "VO10"],
           ["VT10", "VY10"], ["WD10", "WI10"],
           ["WN10", "WS10"], ["WX10", "XC10"], ["XH10", "XM10"],
           ["XR10", "XW10"], ["YB10", "YG10"],
           ["YL10", "YQ10"], ["YV10", "ZA10"], ["ZF10", "ZK10"],
           ["ZP10", "ZU10"], ["ZZ10", "AAE10"], ["AAJ10", "AAO10"],
           ["AAT10", "AAY10"], ["ABD10", "ABI10"],
           ['ABN10', 'ABS10'], ['ABX10', 'ACC10'],
           ['ACH10', 'ACM10'],
           ['ACR10', 'ACW10'], ['ADB10', 'ADG10'],
           ['ADL10', 'ADQ10'], ['ADV10', 'AEA10'],
           ['AEF10', 'AEK10'], ['AEP10', 'AEU10'],
           ['AEZ10', 'AFE10'], ['AFJ10', 'AFO10'],
           ['AFT10', 'AFY10'], ['AGD10', 'AGI10'],
           ['AGN10', 'AGS10'], ['AGX10', 'AHC10'],
           ['AHH10', 'AHM10'], ['AHR10', 'AHW10'],
           ['AIB10', 'AIG10'], ['AIL10', 'AIQ10'],
           ['AIV10', 'AJA10'], ['AJF10', 'AJK10'],
           ['AJP10', 'AJU10'], ['AJZ10', 'AKE10'],
           ['AKJ10', 'AKO10'], ['AKT10', 'AKY10'],
           ['ALD10', 'ALI10'], ['ALN10', 'ALS10'],
           ['ALX10', 'AMC10'], ['AMH10', 'AMM10'],
           ['AMR10', 'AMW10'], ['ANB10', 'ANG10']]

pic_2_4_merged = [["AP15", "AU15"], ["AZ15", "BE15"],
                  ["BJ15", "BO15"], ["BT15", "BY15"], ["CD15", "CI15"],
                  ["CN15", "CS15"], ["CX15", "DC15"],
                  ["DH15", "DM15"], ["DR15", "DW15"], ["EB15", "EG15"],
                  ["EL15", "EQ15"], ["EV15", "FA15"],
                  ["FF15", "FK15"], ["FP15", "FU15"], ["FZ15", "GE15"],
                  ["GJ15", "GO15"], ["GT15", "GY15"],
                  ["HD15", "HI15"], ["HN15", "HS15"], ["HX15", "IC15"],
                  ["IH15", "IM15"], ["IR15", "IW15"],
                  ["JB15", "JG15"], ["JL15", "JQ15"], ["JV15", "KA15"],
                  ["KF15", "KK15"], ["KP15", "KU15"],
                  ["KZ15", "LE15"], ["LJ15", "LO15"], ["LT15", "LY15"],
                  ["MD15", "MI15"], ["MN15", "MS15"],
                  ["MX15", "NC15"], ["NH15", "NM15"], ["NR15", "NW15"],
                  ["OB15", "OG15"], ["OL15", "OQ15"],
                  ["OV15", "PA15"], ["PF15", "PK15"], ["PP15", "PU15"],
                  ["PZ15", "QE15"], ["QJ15", "QO15"],
                  ["QT15", "QY15"], ["RD15", "RI15"], ["RN15", "RS15"],
                  ["RX15", "SC15"], ["SH15", "SM15"],
                  ["SR15", "SW15"], ["TB15", "TG15"], ["TL15", "TQ15"],
                  ["TV15", "UA15"], ["UF15", "UK15"],
                  ["UP15", "UU15"], ["UZ15", "VE15"], ["VJ15", "VO15"],
                  ["VT15", "VY15"], ["WD15", "WI15"],
                  ["WN15", "WS15"], ["WX15", "XC15"], ["XH15", "XM15"],
                  ["XR15", "XW15"], ["YB15", "YG15"],
                  ["YL15", "YQ15"], ["YV15", "ZA15"], ["ZF15", "ZK15"],
                  ["ZP15", "ZU15"], ["ZZ15", "AAE15"], ["AAJ15", "AAO15"],
                  ["AAT15", "AAY15"], ["ABD15", "ABI15"],
                  ['ABN15', 'ABS15'], ['ABX15', 'ACC15'],
                  ['ACH15', 'ACM15'],
                  ['ACR15', 'ACW15'], ['ADB15', 'ADG15'],
                  ['ADL15', 'ADQ15'], ['ADV15', 'AEA15'],
                  ['AEF15', 'AEK15'], ['AEP15', 'AEU15'],
                  ['AEZ15', 'AFE15'], ['AFJ15', 'AFO15'],
                  ['AFT15', 'AFY15'], ['AGD15', 'AGI15'],
                  ['AGN15', 'AGS15'], ['AGX15', 'AHC15'],
                  ['AHH15', 'AHM15'], ['AHR15', 'AHW15'],
                  ['AIB15', 'AIG15'], ['AIL15', 'AIQ15'],
                  ['AIV15', 'AJA15'], ['AJF15', 'AJK15'],
                  ['AJP15', 'AJU15'], ['AJZ15', 'AKE15'],
                  ['AKJ15', 'AKO15'], ['AKT15', 'AKY15'],
                  ['ALD15', 'ALI15'], ['ALN15', 'ALS15'],
                  ['ALX15', 'AMC15'], ['AMH15', 'AMM15'],
                  ['AMR15', 'AMW15']]

pic_1_4 = [["AU10", "AU15"], ["BE10", "BE15"],
           ["BO10", "BO15"], ["BY10", "BY15"], ["CI10", "CI15"],
           ["CS10", "CS15"], ["DC10", "DC15"],
           ["DM10", "DM15"], ["DW10", "DW15"], ["EG10", "EG15"],
           ["EQ10", "EQ15"], ["FA10", "FA15"],
           ["FK10", "FK15"], ["FU10", "FU15"], ["GE10", "GE15"],
           ["GO10", "GO15"], ["GY10", "GY15"],
           ["HI10", "HI15"], ["HS10", "HS15"], ["IC10", "IC15"],
           ["IM10", "IM15"], ["IW10", "IW15"],
           ["JG10", "JG15"], ["JQ10", "JQ15"], ["KA10", "KA15"],
           ["KK10", "KK15"], ["KU10", "KU15"],
           ["LE10", "LE15"], ["LO10", "LO15"], ["LY10", "LY15"],
           ["MI10", "MI15"], ["MS10", "MS15"],
           ["NC10", "NC15"], ["NM10", "NM15"], ["NW10", "NW15"],
           ["OG10", "OG15"], ["OQ10", "OQ15"],
           ["PA10", "PA15"], ["PK10", "PK15"], ["PU10", "PU15"],
           ["QE10", "QE15"], ["QO10", "QO15"],
           ["QY10", "QY15"], ["RI10", "RI15"], ["RS10", "RS15"],
           ["SC10", "SC15"], ["SM10", "SM15"],
           ["SW10", "SW15"], ["TG10", "TG15"], ["TQ10", "TQ15"],
           ["UA10", "UA15"], ["UK10", "UK15"],
           ["UU10", "UU15"], ["VE10", "VE15"], ["VO10", "VO15"],
           ["VY10", "VY15"], ["WI10", "WI15"],
           ["WS10", "WS15"], ["XC10", "XC15"], ["XM10", "XM15"],
           ["XW10", "XW15"], ["YG10", "YG15"],
           ["YQ10", "YQ15"], ["ZA10", "ZA15"], ["ZK10", "ZK15"],
           ["ZU10", "ZU15"], ["AAE10", "AAE15"], ["AAO10", "AAO15"],
           ["AAY10", "AAY15"], ["ABI10", "ABI15"],
           ['ABS10', 'ABS15'], ['ACC10', 'ACC15'],
           ['ACM10', 'ACM15'],
           ['ACW10', 'ACW15'], ['ADG10', 'ADG15'],
           ['ADQ10', 'ADQ15'], ['AEA10', 'AEA15'],
           ['AEK10', 'AEK15'], ['AEU10', 'AEU15'],
           ['AFE10', 'AFE15'], ['AFO10', 'AFO15'],
           ['AFY10', 'AFY15'], ['AGI10', 'AGI15'],
           ['AGS10', 'AGS15'], ['AHC10', 'AHC15'],
           ['AHM10', 'AHM15'], ['AHW10', 'AHW15'],
           ['AIG10', 'AIG15'], ['AIQ10', 'AIQ15'],
           ['AJA10', 'AJA15'], ['AJK10', 'AJK15'],
           ['AJU10', 'AJU15'], ['AKE10', 'AKE15'],
           ['AKO10', 'AKO15'], ['AKY10', 'AKY15'],
           ['ALI10', 'ALI15'], ['ALS10', 'ALS15'],
           ['AMC10', 'AMC15'], ['AMM10', 'AMM15'],
           ['AMW10', 'AMW15'], ['ANG10', 'ANG15']]

pic_4_5 = [["AZ10", "BE10", "AZ15", "BE15"],
           ["BJ10", "BO10", "BJ15", "BO15"], ["BT10", "BY10", "BT15", "BY15"],
           ["CD10", "CI10", "CD15", "CI15"], ["CN10", "CS10", "CN15", "CS15"],
           ["CX10", "DC10", "CX15", "DC15"],
           ["DH10", "DM10", "DH15", "DM15"], ["DR10", "DW10", "DR15", "DW15"],
           ["EB10", "EG10", "EB15", "EG15"], ["EL10", "EQ10", "EL15", "EQ15"],
           ["EV10", "FA10", "EV15", "FA15"],
           ["FF10", "FK10", "FF15", "FK15"], ["FP10", "FU10", "FP15", "FU15"],
           ["FZ10", "GE10", "FZ15", "GE15"], ["GJ10", "GO10", "GJ15", "GO15"],
           ["GT10", "GY10", "GT15", "GY15"],
           ["HD10", "HI10", "HD15", "HI15"], ["HN10", "HS10", "HN15", "HS15"],
           ["HX10", "IC10", "HX15", "IC15"], ["IH10", "IM10", "IH15", "IM15"],
           ["IR10", "IW10", "IR15", "IW15"],
           ["JB10", "JG10", "JB15", "JG15"], ["JL10", "JQ10", "JL15", "JQ15"],
           ["JV10", "KA10", "JV15", "KA15"], ["KF10", "KK10", "KF15", "KK15"],
           ["KP10", "KU10", "KP15", "KU15"],
           ["KZ10", "LE10", "KZ15", "LE15"], ["LJ10", "LO10", "LJ15", "LO15"],
           ["LT10", "LY10", "LT15", "LY15"], ["MD10", "MI10", "MD15", "MI15"],
           ["MN10", "MS10", "MN15", "MS15"],
           ["MX10", "NC10", "MX15", "NC15"], ["NH10", "NM10", "NH15", "NM15"],
           ["NR10", "NW10", "NR15", "NW15"], ["OB10", "OG10", "OB15", "OG15"],
           ["OL10", "OQ10", "OL15", "OQ15"],
           ["OV10", "PA10", "OV15", "PA15"], ["PF10", "PK10", "PF15", "PK15"],
           ["PP10", "PU10", "PP15", "PU15"], ["PZ10", "QE10", "PZ15", "QE15"],
           ["QJ10", "QO10", "QJ15", "QO15"],
           ["QT10", "QY10", "QT15", "QY15"], ["RD10", "RI10", "RD15", "RI15"],
           ["RN10", "RS10", "RN15", "RS15"], ["RX10", "SC10", "RX15", "SC15"],
           ["SH10", "SM10", "SH15", "SM15"],
           ["SR10", "SW10", "SR15", "SW15"], ["TB10", "TG10", "TB15", "TG15"],
           ["TL10", "TQ10", "TL15", "TQ15"], ["TV10", "UA10", "TV15", "UA15"],
           ["UF10", "UK10", "UF15", "UK15"],
           ["UP10", "UU10", "UP15", "UU15"], ["UZ10", "VE10", "UZ15", "VE15"],
           ["VJ10", "VO10", "VJ15", "VO15"], ["VT10", "VY10", "VT15", "VY15"],
           ["WD10", "WI10", "WD15", "WI15"],
           ["WN10", "WS10", "WN15", "WS15"], ["WX10", "XC10", "WX15", "XC15"],
           ["XH10", "XM10", "XH15", "XM15"], ["XR10", "XW10", "XR15", "XW15"],
           ["YB10", "YG10", "YB15", "YG15"],
           ["YL10", "YQ10", "YL15", "YQ15"], ["YV10", "ZA10", "YV15", "ZA15"],
           ["ZF10", "ZK10", "ZF15", "ZK15"], ["ZP10", "ZU10", "ZP15", "ZU15"],
           ["ZZ10", "AAE10", "ZZ15", "AAE15"],
           ["AAJ10", "AAO10", "AAJ15", "AAO15"],
           ["AAT10", "AAY10", "AAT15", "AAY15"],
           ["ABD10", "ABI10", "ABD15", "ABI15"],
           ['ABN10', 'ABS10', 'ABN15', 'ABS15'],
           ['ABX10', 'ACC10', 'ABX15', 'ACC15'],
           ['ACH10', 'ACM10', 'ACH15', 'ACM15'],
           ['ACR10', 'ACW10', 'ACR15', 'ACW10'],
           ['ADB10', 'ADG10', 'ADB15', 'ADG15'],
           ['ADL10', 'ADQ10', 'ADL15', 'ADQ15'],
           ['ADV10', 'AEA10', 'ADV15', 'AEA15'],
           ['AEF10', 'AEK10', 'AEF15', 'AEK15'],
           ['AEP10', 'AEU10', 'AEP15', 'AEU15'],
           ['AEZ10', 'AFE10', 'AEZ15', 'AFE15'],
           ['AFJ10', 'AFO10', 'AFJ15', 'AFO15'],
           ['AFT10', 'AFY10', 'AFT15', 'AFY15'],
           ['AGD10', 'AGI10', 'AGD15', 'AGI15'],
           ['AGN10', 'AGS10', 'AGN15', 'AGS15'],
           ['AGX10', 'AHC10', 'AGX15', 'AHC15'],
           ['AHH10', 'AHM10', 'AHH15', 'AHM15'],
           ['AHR10', 'AHW10', 'AHR15', 'AHW15'],
           ['AIB10', 'AIG10', 'AIB15', 'AIG15'],
           ['AIL10', 'AIQ10', 'AIL15', 'AIQ15'],
           ['AIV10', 'AJA10', 'AIV15', 'AJA15'],
           ['AJF10', 'AJK10', 'AJF15', 'AJK15'],
           ['AJP10', 'AJU10', 'AJP15', 'AJU15'],
           ['AJZ10', 'AKE10', 'AJZ15', 'AKE15'],
           ['AKJ10', 'AKO10', 'AKJ15', 'AKO15'],
           ['AKT10', 'AKY10', 'AKT15', 'AKY15'],
           ['ALD10', 'ALI10', 'ALD15', 'ALI15'],
           ['ALN10', 'ALS10', 'ALN15', 'ALS15'],
           ['ALX10', 'AMC10', 'ALX15', 'AMC15'],
           ['AMH10', 'AMM10', 'AMH15', 'AMM15'],
           ['AMR10', 'AMW10', 'AMR15', 'AMW15'],
           ['ANB10', 'ANG10', 'ANB15', 'ANG15']]

pic_3_5 = [["AZ10", "AZ15", "BE15"],
           ["BJ10", "BJ15", "BO15"], ["BT10", "BT15", "BY15"],
           ["CD10", "CD15", "CI15"], ["CN10", "CN15", "CS15"],
           ["CX10", "CX15", "DC15"],
           ["DH10", "DH15", "DM15"], ["DR10", "DR15", "DW15"],
           ["EB10", "EB15", "EG15"], ["EL10", "EL15", "EQ15"],
           ["EV10", "EV15", "FA15"],
           ["FF10", "FF15", "FK15"], ["FP10", "FP15", "FU15"],
           ["FZ10", "FZ15", "GE15"], ["GJ10", "GJ15", "GO15"],
           ["GT10", "GT15", "GY15"],
           ["HD10", "HD15", "HI15"], ["HN10", "HN15", "HS15"],
           ["HX10", "HX15", "IC15"], ["IH10", "IH15", "IM15"],
           ["IR10", "IR15", "IW15"],
           ["JB10", "JB15", "JG15"], ["JL10", "JL15", "JQ15"],
           ["JV10", "JV15", "KA15"], ["KF10", "KF15", "KK15"],
           ["KP10", "KP15", "KU15"],
           ["KZ10", "KZ15", "LE15"], ["LJ10", "LJ15", "LO15"],
           ["LT10", "LT15", "LY15"], ["MD10", "MD15", "MI15"],
           ["MN10", "MN15", "MS15"],
           ["MX10", "MX15", "NC15"], ["NH10", "NH15", "NM15"],
           ["NR10", "NR15", "NW15"], ["OB10", "OB15", "OG15"],
           ["OL10", "OL15", "OQ15"],
           ["OV10", "OV15", "PA15"], ["PF10", "PF15", "PK15"],
           ["PP10", "PP15", "PU15"], ["PZ10", "PZ15", "QE15"],
           ["QJ10", "QJ15", "QO15"],
           ["QT10", "QT15", "QY15"], ["RD10", "RD15", "RI15"],
           ["RN10", "RN15", "RS15"], ["RX10", "RX15", "SC15"],
           ["SH10", "SH15", "SM15"],
           ["SR10", "SR15", "SW15"], ["TB10", "TB15", "TG15"],
           ["TL10", "TL15", "TQ15"], ["TV10", "TV15", "UA15"],
           ["UF10", "UF15", "UK15"],
           ["UP10", "UP15", "UU15"], ["UZ10", "UZ15", "VE15"],
           ["VJ10", "VJ15", "VO15"], ["VT10", "VT15", "VY15"],
           ["WD10", "WD15", "WI15"],
           ["WN10", "WN15", "WS15"], ["WX10", "WX15", "XC15"],
           ["XH10", "XH15", "XM15"], ["XR10", "XR15", "XW15"],
           ["YB10", "YB15", "YG15"],
           ["YL10", "YL15", "YQ15"], ["YV10", "YV15", "ZA15"],
           ["ZF10", "ZF15", "ZK15"], ["ZP10", "ZP15", "ZU15"],
           ["ZZ10", "ZZ15", "AAE15"], ["AAJ10", "AAJ15", "AAO15"],
           ["AAT10", "AAT15", "AAY15"], ["ABD10", "ABD15", "ABI15"],
           ['ABN10', 'ABN15', 'ABS15'], ['ABX10', 'ABX15', 'ACC15'],
           ['ACH10', 'ACH15', 'ACM15'],
           ['ACR10', 'ACR15', 'ACW10'], ['ADB10', 'ADB15', 'ADG15'],
           ['ADL10', 'ADL15', 'ADQ15'], ['ADV10', 'ADV15', 'AEA15'],
           ['AEF10', 'AEF15', 'AEK15'], ['AEP10', 'AEP15', 'AEU15'],
           ['AEZ10', 'AEZ15', 'AFE15'], ['AFJ10', 'AFJ15', 'AFO15'],
           ['AFT10', 'AFT15', 'AFY15'], ['AGD10', 'AGD15', 'AGI15'],
           ['AGN10', 'AGN15', 'AGS15'], ['AGX10', 'AGX15', 'AHC15'],
           ['AHH10', 'AHH15', 'AHM15'], ['AHR10', 'AHR15', 'AHW15'],
           ['AIB10', 'AIB15', 'AIG15'], ['AIL10', 'AIL15', 'AIQ15'],
           ['AIV10', 'AIV15', 'AJA15'], ['AJF10', 'AJF15', 'AJK15'],
           ['AJP10', 'AJP15', 'AJU15'], ['AJZ10', 'AJZ15', 'AKE15'],
           ['AKJ10', 'AKJ15', 'AKO15'], ['AKT10', 'AKT15', 'AKY15'],
           ['ALD10', 'ALD15', 'ALI15'], ['ALN10', 'ALN15', 'ALS15'],
           ['ALX10', 'ALX15', 'AMC15'], ['AMH10', 'AMH15', 'AMM15'],
           ['AMR10', 'AMR15', 'AMW15'], ['ANB10', 'ANB15', 'ANG15'],
           ['ANL10', 'ANL15', 'ANG15']]

pic_2_5 = [["AZ10", "BE10"],
           ["BJ10", "BO10"], ["BT10", "BY10"], ["CD10", "CI10"],
           ["CN10", "CS10"], ["CX10", "DC10"],
           ["DH10", "DM10"], ["DR10", "DW10"], ["EB10", "EG10"],
           ["EL10", "EQ10"], ["EV10", "FA10"],
           ["FF10", "FK10"], ["FP10", "FU10"], ["FZ10", "GE10"],
           ["GJ10", "GO10"], ["GT10", "GY10"],
           ["HD10", "HI10"], ["HN10", "HS10"], ["HX10", "IC10"],
           ["IH10", "IM10"], ["IR10", "IW10"],
           ["JB10", "JG10"], ["JL10", "JQ10"], ["JV10", "KA10"],
           ["KF10", "KK10"], ["KP10", "KU10"],
           ["KZ10", "LE10"], ["LJ10", "LO10"], ["LT10", "LY10"],
           ["MD10", "MI10"], ["MN10", "MS10"],
           ["MX10", "NC10"], ["NH10", "NM10"], ["NR10", "NW10"],
           ["OB10", "OG10"], ["OL10", "OQ10"],
           ["OV10", "PA10"], ["PF10", "PK10"], ["PP10", "PU10"],
           ["PZ10", "QE10"], ["QJ10", "QO10"],
           ["QT10", "QY10"], ["RD10", "RI10"], ["RN10", "RS10"],
           ["RX10", "SC10"], ["SH10", "SM10"],
           ["SR10", "SW10"], ["TB10", "TG10"], ["TL10", "TQ10"],
           ["TV10", "UA10"], ["UF10", "UK10"],
           ["UP10", "UU10"], ["UZ10", "VE10"], ["VJ10", "VO10"],
           ["VT10", "VY10"], ["WD10", "WI10"],
           ["WN10", "WS10"], ["WX10", "XC10"], ["XH10", "XM10"],
           ["XR10", "XW10"], ["YB10", "YG10"],
           ["YL10", "YQ10"], ["YV10", "ZA10"], ["ZF10", "ZK10"],
           ["ZP10", "ZU10"], ["ZZ10", "AAE10"], ["AAJ10", "AAO10"],
           ["AAT10", "AAY10"], ["ABD10", "ABI10"],
           ['ABN10', 'ABS10'], ['ABX10', 'ACC10'],
           ['ACH10', 'ACM10'],
           ['ACR10', 'ACW10'], ['ADB10', 'ADG10'],
           ['ADL10', 'ADQ10'], ['ADV10', 'AEA10'],
           ['AEF10', 'AEK10'], ['AEP10', 'AEU10'],
           ['AEZ10', 'AFE10'], ['AFJ10', 'AFO10'],
           ['AFT10', 'AFY10'], ['AGD10', 'AGI10'],
           ['AGN10', 'AGS10'], ['AGX10', 'AHC10'],
           ['AHH10', 'AHM10'], ['AHR10', 'AHW10'],
           ['AIB10', 'AIG10'], ['AIL10', 'AIQ10'],
           ['AIV10', 'AJA10'], ['AJF10', 'AJK10'],
           ['AJP10', 'AJU10'], ['AJZ10', 'AKE10'],
           ['AKJ10', 'AKO10'], ['AKT10', 'AKY10'],
           ['ALD10', 'ALI10'], ['ALN10', 'ALS10'],
           ['ALX10', 'AMC10'], ['AMH10', 'AMM10'],
           ['AMR10', 'AMW10'], ['ANB10', 'ANG10']]

pic_2_5_merged = [["AZ15", "BE15"],
                  ["BJ15", "BO15"], ["BT15", "BY15"], ["CD15", "CI15"],
                  ["CN15", "CS15"], ["CX15", "DC15"],
                  ["DH15", "DM15"], ["DR15", "DW15"], ["EB15", "EG15"],
                  ["EL15", "EQ15"], ["EV15", "FA15"],
                  ["FF15", "FK15"], ["FP15", "FU15"], ["FZ15", "GE15"],
                  ["GJ15", "GO15"], ["GT15", "GY15"],
                  ["HD15", "HI15"], ["HN15", "HS15"], ["HX15", "IC15"],
                  ["IH15", "IM15"], ["IR15", "IW15"],
                  ["JB15", "JG15"], ["JL15", "JQ15"], ["JV15", "KA15"],
                  ["KF15", "KK15"], ["KP15", "KU15"],
                  ["KZ15", "LE15"], ["LJ15", "LO15"], ["LT15", "LY15"],
                  ["MD15", "MI15"], ["MN15", "MS15"],
                  ["MX15", "NC15"], ["NH15", "NM15"], ["NR15", "NW15"],
                  ["OB15", "OG15"], ["OL15", "OQ15"],
                  ["OV15", "PA15"], ["PF15", "PK15"], ["PP15", "PU15"],
                  ["PZ15", "QE15"], ["QJ15", "QO15"],
                  ["QT15", "QY15"], ["RD15", "RI15"], ["RN15", "RS15"],
                  ["RX15", "SC15"], ["SH15", "SM15"],
                  ["SR15", "SW15"], ["TB15", "TG15"], ["TL15", "TQ15"],
                  ["TV15", "UA15"], ["UF15", "UK15"],
                  ["UP15", "UU15"], ["UZ15", "VE15"], ["VJ15", "VO15"],
                  ["VT15", "VY15"], ["WD15", "WI15"],
                  ["WN15", "WS15"], ["WX15", "XC15"], ["XH15", "XM15"],
                  ["XR15", "XW15"], ["YB15", "YG15"],
                  ["YL15", "YQ15"], ["YV15", "ZA15"], ["ZF15", "ZK15"],
                  ["ZP15", "ZU15"], ["ZZ15", "AAE15"], ["AAJ15", "AAO15"],
                  ["AAT15", "AAY15"], ["ABD15", "ABI15"],
                  ['ABN15', 'ABS15'], ['ABX15', 'ACC15'],
                  ['ACH15', 'ACM15'],
                  ['ACR15', 'ACW15'], ['ADB15', 'ADG15'],
                  ['ADL15', 'ADQ15'], ['ADV15', 'AEA15'],
                  ['AEF15', 'AEK15'], ['AEP15', 'AEU15'],
                  ['AEZ15', 'AFE15'], ['AFJ15', 'AFO15'],
                  ['AFT15', 'AFY15'], ['AGD15', 'AGI15'],
                  ['AGN15', 'AGS15'], ['AGX15', 'AHC15'],
                  ['AHH15', 'AHM15'], ['AHR15', 'AHW15'],
                  ['AIB15', 'AIG15'], ['AIL15', 'AIQ15'],
                  ['AIV15', 'AJA15'], ['AJF15', 'AJK15'],
                  ['AJP15', 'AJU15'], ['AJZ15', 'AKE15'],
                  ['AKJ15', 'AKO15'], ['AKT15', 'AKY15'],
                  ['ALD15', 'ALI15'], ['ALN15', 'ALS15'],
                  ['ALX15', 'AMC15'], ['AMH15', 'AMM15'],
                  ['AMR15', 'AMW15'], ['ANB15', 'ANG15']]

pic_1_5 = [["BE10", "BE15"],
           ["BO10", "BO15"], ["BY10", "BY15"], ["CI10", "CI15"],
           ["CS10", "CS15"], ["DC10", "DC15"],
           ["DM10", "DM15"], ["DW10", "DW15"], ["EG10", "EG15"],
           ["EQ10", "EQ15"], ["FA10", "FA15"],
           ["FK10", "FK15"], ["FU10", "FU15"], ["GE10", "GE15"],
           ["GO10", "GO15"], ["GY10", "GY15"],
           ["HI10", "HI15"], ["HS10", "HS15"], ["IC10", "IC15"],
           ["IM10", "IM15"], ["IW10", "IW15"],
           ["JG10", "JG15"], ["JQ10", "JQ15"], ["KA10", "KA15"],
           ["KK10", "KK15"], ["KU10", "KU15"],
           ["LE10", "LE15"], ["LO10", "LO15"], ["LY10", "LY15"],
           ["MI10", "MI15"], ["MS10", "MS15"],
           ["NC10", "NC15"], ["NM10", "NM15"], ["NW10", "NW15"],
           ["OG10", "OG15"], ["OQ10", "OQ15"],
           ["PA10", "PA15"], ["PK10", "PK15"], ["PU10", "PU15"],
           ["QE10", "QE15"], ["QO10", "QO15"],
           ["QY10", "QY15"], ["RI10", "RI15"], ["RS10", "RS15"],
           ["SC10", "SC15"], ["SM10", "SM15"],
           ["SW10", "SW15"], ["TG10", "TG15"], ["TQ10", "TQ15"],
           ["UA10", "UA15"], ["UK10", "UK15"],
           ["UU10", "UU15"], ["VE10", "VE15"], ["VO10", "VO15"],
           ["VY10", "VY15"], ["WI10", "WI15"],
           ["WS10", "WS15"], ["XC10", "XC15"], ["XM10", "XM15"],
           ["XW10", "XW15"], ["YG10", "YG15"],
           ["YQ10", "YQ15"], ["ZA10", "ZA15"], ["ZK10", "ZK15"],
           ["ZU10", "ZU15"], ["AAE10", "AAE15"], ["AAO10", "AAO15"],
           ["AAY10", "AAY15"], ["ABI10", "ABI15"],
           ['ABS10', 'ABS15'], ['ACC10', 'ACC15'],
           ['ACM10', 'ACM15'],
           ['ACW10', 'ACW15'], ['ADG10', 'ADG15'],
           ['ADQ10', 'ADQ15'], ['AEA10', 'AEA15'],
           ['AEK10', 'AEK15'], ['AEU10', 'AEU15'],
           ['AFE10', 'AFE15'], ['AFO10', 'AFO15'],
           ['AFY10', 'AFY15'], ['AGI10', 'AGI15'],
           ['AGS10', 'AGS15'], ['AHC10', 'AHC15'],
           ['AHM10', 'AHM15'], ['AHW10', 'AHW15'],
           ['AIG10', 'AIG15'], ['AIQ10', 'AIQ15'],
           ['AJA10', 'AJA15'], ['AJK10', 'AJK15'],
           ['AJU10', 'AJU15'], ['AKE10', 'AKE15'],
           ['AKO10', 'AKO15'], ['AKY10', 'AKY15'],
           ['ALI10', 'ALI15'], ['ALS10', 'ALS15'],
           ['AMC10', 'AMC15'], ['AMM10', 'AMM15'],
           ['AMW10', 'AMW15'], ['ANG10', 'ANG15']]

pic_4_6 = [
    ["BJ10", "BO10", "BJ15", "BO15"], ["BT10", "BY10", "BT15", "BY15"],
    ["CD10", "CI10", "CD15", "CI15"], ["CN10", "CS10", "CN15", "CS15"],
    ["CX10", "DC10", "CX15", "DC15"],
    ["DH10", "DM10", "DH15", "DM15"], ["DR10", "DW10", "DR15", "DW15"],
    ["EB10", "EG10", "EB15", "EG15"], ["EL10", "EQ10", "EL15", "EQ15"],
    ["EV10", "FA10", "EV15", "FA15"],
    ["FF10", "FK10", "FF15", "FK15"], ["FP10", "FU10", "FP15", "FU15"],
    ["FZ10", "GE10", "FZ15", "GE15"], ["GJ10", "GO10", "GJ15", "GO15"],
    ["GT10", "GY10", "GT15", "GY15"],
    ["HD10", "HI10", "HD15", "HI15"], ["HN10", "HS10", "HN15", "HS15"],
    ["HX10", "IC10", "HX15", "IC15"], ["IH10", "IM10", "IH15", "IM15"],
    ["IR10", "IW10", "IR15", "IW15"],
    ["JB10", "JG10", "JB15", "JG15"], ["JL10", "JQ10", "JL15", "JQ15"],
    ["JV10", "KA10", "JV15", "KA15"], ["KF10", "KK10", "KF15", "KK15"],
    ["KP10", "KU10", "KP15", "KU15"],
    ["KZ10", "LE10", "KZ15", "LE15"], ["LJ10", "LO10", "LJ15", "LO15"],
    ["LT10", "LY10", "LT15", "LY15"], ["MD10", "MI10", "MD15", "MI15"],
    ["MN10", "MS10", "MN15", "MS15"],
    ["MX10", "NC10", "MX15", "NC15"], ["NH10", "NM10", "NH15", "NM15"],
    ["NR10", "NW10", "NR15", "NW15"], ["OB10", "OG10", "OB15", "OG15"],
    ["OL10", "OQ10", "OL15", "OQ15"],
    ["OV10", "PA10", "OV15", "PA15"], ["PF10", "PK10", "PF15", "PK15"],
    ["PP10", "PU10", "PP15", "PU15"], ["PZ10", "QE10", "PZ15", "QE15"],
    ["QJ10", "QO10", "QJ15", "QO15"],
    ["QT10", "QY10", "QT15", "QY15"], ["RD10", "RI10", "RD15", "RI15"],
    ["RN10", "RS10", "RN15", "RS15"], ["RX10", "SC10", "RX15", "SC15"],
    ["SH10", "SM10", "SH15", "SM15"],
    ["SR10", "SW10", "SR15", "SW15"], ["TB10", "TG10", "TB15", "TG15"],
    ["TL10", "TQ10", "TL15", "TQ15"], ["TV10", "UA10", "TV15", "UA15"],
    ["UF10", "UK10", "UF15", "UK15"],
    ["UP10", "UU10", "UP15", "UU15"], ["UZ10", "VE10", "UZ15", "VE15"],
    ["VJ10", "VO10", "VJ15", "VO15"], ["VT10", "VY10", "VT15", "VY15"],
    ["WD10", "WI10", "WD15", "WI15"],
    ["WN10", "WS10", "WN15", "WS15"], ["WX10", "XC10", "WX15", "XC15"],
    ["XH10", "XM10", "XH15", "XM15"], ["XR10", "XW10", "XR15", "XW15"],
    ["YB10", "YG10", "YB15", "YG15"],
    ["YL10", "YQ10", "YL15", "YQ15"], ["YV10", "ZA10", "YV15", "ZA15"],
    ["ZF10", "ZK10", "ZF15", "ZK15"], ["ZP10", "ZU10", "ZP15", "ZU15"],
    ["ZZ10", "AAE10", "ZZ15", "AAE15"],
    ["AAJ10", "AAO10", "AAJ15", "AAO15"], ["AAT10", "AAY10", "AAT15", "AAY15"],
    ["ABD10", "ABI10", "ABD15", "ABI15"], ['ABN10', 'ABS10', 'ABN15', 'ABS15'],
    ['ABX10', 'ACC10', 'ABX15', 'ACC15'], ['ACH10', 'ACM10', 'ACH15', 'ACM15'],
    ['ACR10', 'ACW10', 'ACR15', 'ACW10'], ['ADB10', 'ADG10', 'ADB15', 'ADG15'],
    ['ADL10', 'ADQ10', 'ADL15', 'ADQ15'], ['ADV10', 'AEA10', 'ADV15', 'AEA15'],
    ['AEF10', 'AEK10', 'AEF15', 'AEK15'], ['AEP10', 'AEU10', 'AEP15', 'AEU15'],
    ['AEZ10', 'AFE10', 'AEZ15', 'AFE15'], ['AFJ10', 'AFO10', 'AFJ15', 'AFO15'],
    ['AFT10', 'AFY10', 'AFT15', 'AFY15'], ['AGD10', 'AGI10', 'AGD15', 'AGI15'],
    ['AGN10', 'AGS10', 'AGN15', 'AGS15'], ['AGX10', 'AHC10', 'AGX15', 'AHC15'],
    ['AHH10', 'AHM10', 'AHH15', 'AHM15'], ['AHR10', 'AHW10', 'AHR15', 'AHW15'],
    ['AIB10', 'AIG10', 'AIB15', 'AIG15'], ['AIL10', 'AIQ10', 'AIL15', 'AIQ15'],
    ['AIV10', 'AJA10', 'AIV15', 'AJA15'], ['AJF10', 'AJK10', 'AJF15', 'AJK15'],
    ['AJP10', 'AJU10', 'AJP15', 'AJU15'], ['AJZ10', 'AKE10', 'AJZ15', 'AKE15'],
    ['AKJ10', 'AKO10', 'AKJ15', 'AKO15'], ['AKT10', 'AKY10', 'AKT15', 'AKY15'],
    ['ALD10', 'ALI10', 'ALD15', 'ALI15'], ['ALN10', 'ALS10', 'ALN15', 'ALS15'],
    ['ALX10', 'AMC10', 'ALX15', 'AMC15'], ['AMH10', 'AMM10', 'AMH15', 'AMM15'],
    ['AMR10', 'AMW10', 'AMR15', 'AMW15'], ['ANB10', 'ANG10', 'ANB15', 'ANG15'],
    ['ANL10', 'ANQ10', 'ANL15', 'ANG15']
]

pic_3_6 = [
    ["BJ10", "BJ15", "BO15"], ["BT10", "BT15", "BY15"],
    ["CD10", "CD15", "CI15"], ["CN10", "CN15", "CS15"],
    ["CX10", "CX15", "DC15"],
    ["DH10", "DH15", "DM15"], ["DR10", "DR15", "DW15"],
    ["EB10", "EB15", "EG15"], ["EL10", "EL15", "EQ15"],
    ["EV10", "EV15", "FA15"],
    ["FF10", "FF15", "FK15"], ["FP10", "FP15", "FU15"],
    ["FZ10", "FZ15", "GE15"], ["GJ10", "GJ15", "GO15"],
    ["GT10", "GT15", "GY15"],
    ["HD10", "HD15", "HI15"], ["HN10", "HN15", "HS15"],
    ["HX10", "HX15", "IC15"], ["IH10", "IH15", "IM15"],
    ["IR10", "IR15", "IW15"],
    ["JB10", "JB15", "JG15"], ["JL10", "JL15", "JQ15"],
    ["JV10", "JV15", "KA15"], ["KF10", "KF15", "KK15"],
    ["KP10", "KP15", "KU15"],
    ["KZ10", "KZ15", "LE15"], ["LJ10", "LJ15", "LO15"],
    ["LT10", "LT15", "LY15"], ["MD10", "MD15", "MI15"],
    ["MN10", "MN15", "MS15"],
    ["MX10", "MX15", "NC15"], ["NH10", "NH15", "NM15"],
    ["NR10", "NR15", "NW15"], ["OB10", "OB15", "OG15"],
    ["OL10", "OL15", "OQ15"],
    ["OV10", "OV15", "PA15"], ["PF10", "PF15", "PK15"],
    ["PP10", "PP15", "PU15"], ["PZ10", "PZ15", "QE15"],
    ["QJ10", "QJ15", "QO15"],
    ["QT10", "QT15", "QY15"], ["RD10", "RD15", "RI15"],
    ["RN10", "RN15", "RS15"], ["RX10", "RX15", "SC15"],
    ["SH10", "SH15", "SM15"],
    ["SR10", "SR15", "SW15"], ["TB10", "TB15", "TG15"],
    ["TL10", "TL15", "TQ15"], ["TV10", "TV15", "UA15"],
    ["UF10", "UF15", "UK15"],
    ["UP10", "UP15", "UU15"], ["UZ10", "UZ15", "VE15"],
    ["VJ10", "VJ15", "VO15"], ["VT10", "VT15", "VY15"],
    ["WD10", "WD15", "WI15"],
    ["WN10", "WN15", "WS15"], ["WX10", "WX15", "XC15"],
    ["XH10", "XH15", "XM15"], ["XR10", "XR15", "XW15"],
    ["YB10", "YB15", "YG15"],
    ["YL10", "YL15", "YQ15"], ["YV10", "YV15", "ZA15"],
    ["ZF10", "ZF15", "ZK15"], ["ZP10", "ZP15", "ZU15"],
    ["ZZ10", "ZZ15", "AAE15"], ["AAJ10", "AAJ15", "AAO15"],
    ["AAT10", "AAT15", "AAY15"], ["ABD10", "ABD15", "ABI15"],
    ['ABN10', 'ABN15', 'ABS15'], ['ABX10', 'ABX15', 'ACC15'],
    ['ACH10', 'ACH15', 'ACM15'],
    ['ACR10', 'ACR15', 'ACW10'], ['ADB10', 'ADB15', 'ADG15'],
    ['ADL10', 'ADL15', 'ADQ15'], ['ADV10', 'ADV15', 'AEA15'],
    ['AEF10', 'AEF15', 'AEK15'], ['AEP10', 'AEP15', 'AEU15'],
    ['AEZ10', 'AEZ15', 'AFE15'], ['AFJ10', 'AFJ15', 'AFO15'],
    ['AFT10', 'AFT15', 'AFY15'], ['AGD10', 'AGD15', 'AGI15'],
    ['AGN10', 'AGN15', 'AGS15'], ['AGX10', 'AGX15', 'AHC15'],
    ['AHH10', 'AHH15', 'AHM15'], ['AHR10', 'AHR15', 'AHW15'],
    ['AIB10', 'AIB15', 'AIG15'], ['AIL10', 'AIL15', 'AIQ15'],
    ['AIV10', 'AIV15', 'AJA15'], ['AJF10', 'AJF15', 'AJK15'],
    ['AJP10', 'AJP15', 'AJU15'], ['AJZ10', 'AJZ15', 'AKE15'],
    ['AKJ10', 'AKJ15', 'AKO15'], ['AKT10', 'AKT15', 'AKY15'],
    ['ALD10', 'ALD15', 'ALI15'], ['ALN10', 'ALN15', 'ALS15'],
    ['ALX10', 'ALX15', 'AMC15'], ['AMH10', 'AMH15', 'AMM15'],
    ['AMR10', 'AMR15', 'AMW15'], ['ANB10', 'ANB15', 'ANG15'],
    ['ANL10', 'ANL15', 'ANG15']]

pic_2_6 = [
    ["BJ10", "BO10"], ["BT10", "BY10"], ["CD10", "CI10"], ["CN10", "CS10"],
    ["CX10", "DC10"],
    ["DH10", "DM10"], ["DR10", "DW10"], ["EB10", "EG10"], ["EL10", "EQ10"],
    ["EV10", "FA10"],
    ["FF10", "FK10"], ["FP10", "FU10"], ["FZ10", "GE10"], ["GJ10", "GO10"],
    ["GT10", "GY10"],
    ["HD10", "HI10"], ["HN10", "HS10"], ["HX10", "IC10"], ["IH10", "IM10"],
    ["IR10", "IW10"],
    ["JB10", "JG10"], ["JL10", "JQ10"], ["JV10", "KA10"], ["KF10", "KK10"],
    ["KP10", "KU10"],
    ["KZ10", "LE10"], ["LJ10", "LO10"], ["LT10", "LY10"], ["MD10", "MI10"],
    ["MN10", "MS10"],
    ["MX10", "NC10"], ["NH10", "NM10"], ["NR10", "NW10"], ["OB10", "OG10"],
    ["OL10", "OQ10"],
    ["OV10", "PA10"], ["PF10", "PK10"], ["PP10", "PU10"], ["PZ10", "QE10"],
    ["QJ10", "QO10"],
    ["QT10", "QY10"], ["RD10", "RI10"], ["RN10", "RS10"], ["RX10", "SC10"],
    ["SH10", "SM10"],
    ["SR10", "SW10"], ["TB10", "TG10"], ["TL10", "TQ10"], ["TV10", "UA10"],
    ["UF10", "UK10"],
    ["UP10", "UU10"], ["UZ10", "VE10"], ["VJ10", "VO10"], ["VT10", "VY10"],
    ["WD10", "WI10"],
    ["WN10", "WS10"], ["WX10", "XC10"], ["XH10", "XM10"], ["XR10", "XW10"],
    ["YB10", "YG10"],
    ["YL10", "YQ10"], ["YV10", "ZA10"], ["ZF10", "ZK10"], ["ZP10", "ZU10"],
    ["ZZ10", "AAE10"], ["AAJ10", "AAO10"], ["AAT10", "AAY10"],
    ["ABD10", "ABI10"],
    ['ABN10', 'ABS10'], ['ABX10', 'ACC10'],
    ['ACH10', 'ACM10'],
    ['ACR10', 'ACW10'], ['ADB10', 'ADG10'],
    ['ADL10', 'ADQ10'], ['ADV10', 'AEA10'],
    ['AEF10', 'AEK10'], ['AEP10', 'AEU10'],
    ['AEZ10', 'AFE10'], ['AFJ10', 'AFO10'],
    ['AFT10', 'AFY10'], ['AGD10', 'AGI10'],
    ['AGN10', 'AGS10'], ['AGX10', 'AHC10'],
    ['AHH10', 'AHM10'], ['AHR10', 'AHW10'],
    ['AIB10', 'AIG10'], ['AIL10', 'AIQ10'],
    ['AIV10', 'AJA10'], ['AJF10', 'AJK10'],
    ['AJP10', 'AJU10'], ['AJZ10', 'AKE10'],
    ['AKJ10', 'AKO10'], ['AKT10', 'AKY10'],
    ['ALD10', 'ALI10'], ['ALN10', 'ALS10'],
    ['ALX10', 'AMC10'], ['AMH10', 'AMM10'],
    ['AMR10', 'AMW10'], ['ANB10', 'ANG10']]

pic_2_6_merged = [
    ["BJ15", "BO15"], ["BT15", "BY15"], ["CD15", "CI15"], ["CN15", "CS15"],
    ["CX15", "DC15"],
    ["DH15", "DM15"], ["DR15", "DW15"], ["EB15", "EG15"], ["EL15", "EQ15"],
    ["EV15", "FA15"],
    ["FF15", "FK15"], ["FP15", "FU15"], ["FZ15", "GE15"], ["GJ15", "GO15"],
    ["GT15", "GY15"],
    ["HD15", "HI15"], ["HN15", "HS15"], ["HX15", "IC15"], ["IH15", "IM15"],
    ["IR15", "IW15"],
    ["JB15", "JG15"], ["JL15", "JQ15"], ["JV15", "KA15"], ["KF15", "KK15"],
    ["KP15", "KU15"],
    ["KZ15", "LE15"], ["LJ15", "LO15"], ["LT15", "LY15"], ["MD15", "MI15"],
    ["MN15", "MS15"],
    ["MX15", "NC15"], ["NH15", "NM15"], ["NR15", "NW15"], ["OB15", "OG15"],
    ["OL15", "OQ15"],
    ["OV15", "PA15"], ["PF15", "PK15"], ["PP15", "PU15"], ["PZ15", "QE15"],
    ["QJ15", "QO15"],
    ["QT15", "QY15"], ["RD15", "RI15"], ["RN15", "RS15"], ["RX15", "SC15"],
    ["SH15", "SM15"],
    ["SR15", "SW15"], ["TB15", "TG15"], ["TL15", "TQ15"], ["TV15", "UA15"],
    ["UF15", "UK15"],
    ["UP15", "UU15"], ["UZ15", "VE15"], ["VJ15", "VO15"], ["VT15", "VY15"],
    ["WD15", "WI15"],
    ["WN15", "WS15"], ["WX15", "XC15"], ["XH15", "XM15"], ["XR15", "XW15"],
    ["YB15", "YG15"],
    ["YL15", "YQ15"], ["YV15", "ZA15"], ["ZF15", "ZK15"], ["ZP15", "ZU15"],
    ["ZZ15", "AAE15"], ["AAJ15", "AAO15"], ["AAT15", "AAY15"],
    ["ABD15", "ABI15"],
    ['ABN15', 'ABS15'], ['ABX15', 'ACC15'],
    ['ACH15', 'ACM15'],
    ['ACR15', 'ACW15'], ['ADB15', 'ADG15'],
    ['ADL15', 'ADQ15'], ['ADV15', 'AEA15'],
    ['AEF15', 'AEK15'], ['AEP15', 'AEU15'],
    ['AEZ15', 'AFE15'], ['AFJ15', 'AFO15'],
    ['AFT15', 'AFY15'], ['AGD15', 'AGI15'],
    ['AGN15', 'AGS15'], ['AGX15', 'AHC15'],
    ['AHH15', 'AHM15'], ['AHR15', 'AHW15'],
    ['AIB15', 'AIG15'], ['AIL15', 'AIQ15'],
    ['AIV15', 'AJA15'], ['AJF15', 'AJK15'],
    ['AJP15', 'AJU15'], ['AJZ15', 'AKE15'],
    ['AKJ15', 'AKO15'], ['AKT15', 'AKY15'],
    ['ALD15', 'ALI15'], ['ALN15', 'ALS15'],
    ['ALX15', 'AMC15'], ['AMH15', 'AMM15'],
    ['AMR15', 'AMW15'], ['ANB15', 'ANG15']]

pic_1_6 = [
    ["BO10", "BO15"], ["BY10", "BY15"], ["CI10", "CI15"], ["CS10", "CS15"],
    ["DC10", "DC15"],
    ["DM10", "DM15"], ["DW10", "DW15"], ["EG10", "EG15"], ["EQ10", "EQ15"],
    ["FA10", "FA15"],
    ["FK10", "FK15"], ["FU10", "FU15"], ["GE10", "GE15"], ["GO10", "GO15"],
    ["GY10", "GY15"],
    ["HI10", "HI15"], ["HS10", "HS15"], ["IC10", "IC15"], ["IM10", "IM15"],
    ["IW10", "IW15"],
    ["JG10", "JG15"], ["JQ10", "JQ15"], ["KA10", "KA15"], ["KK10", "KK15"],
    ["KU10", "KU15"],
    ["LE10", "LE15"], ["LO10", "LO15"], ["LY10", "LY15"], ["MI10", "MI15"],
    ["MS10", "MS15"],
    ["NC10", "NC15"], ["NM10", "NM15"], ["NW10", "NW15"], ["OG10", "OG15"],
    ["OQ10", "OQ15"],
    ["PA10", "PA15"], ["PK10", "PK15"], ["PU10", "PU15"], ["QE10", "QE15"],
    ["QO10", "QO15"],
    ["QY10", "QY15"], ["RI10", "RI15"], ["RS10", "RS15"], ["SC10", "SC15"],
    ["SM10", "SM15"],
    ["SW10", "SW15"], ["TG10", "TG15"], ["TQ10", "TQ15"], ["UA10", "UA15"],
    ["UK10", "UK15"],
    ["UU10", "UU15"], ["VE10", "VE15"], ["VO10", "VO15"], ["VY10", "VY15"],
    ["WI10", "WI15"],
    ["WS10", "WS15"], ["XC10", "XC15"], ["XM10", "XM15"], ["XW10", "XW15"],
    ["YG10", "YG15"],
    ["YQ10", "YQ15"], ["ZA10", "ZA15"], ["ZK10", "ZK15"], ["ZU10", "ZU15"],
    ["AAE10", "AAE15"], ["AAO10", "AAO15"], ["AAY10", "AAY15"],
    ["ABI10", "ABI15"],
    ['ABS10', 'ABS15'], ['ACC10', 'ACC15'],
    ['ACM10', 'ACM15'],
    ['ACW10', 'ACW15'], ['ADG10', 'ADG15'],
    ['ADQ10', 'ADQ15'], ['AEA10', 'AEA15'],
    ['AEK10', 'AEK15'], ['AEU10', 'AEU15'],
    ['AFE10', 'AFE15'], ['AFO10', 'AFO15'],
    ['AFY10', 'AFY15'], ['AGI10', 'AGI15'],
    ['AGS10', 'AGS15'], ['AHC10', 'AHC15'],
    ['AHM10', 'AHM15'], ['AHW10', 'AHW15'],
    ['AIG10', 'AIG15'], ['AIQ10', 'AIQ15'],
    ['AJA10', 'AJA15'], ['AJK10', 'AJK15'],
    ['AJU10', 'AJU15'], ['AKE10', 'AKE15'],
    ['AKO10', 'AKO15'], ['AKY10', 'AKY15'],
    ['ALI10', 'ALI15'], ['ALS10', 'ALS15'],
    ['AMC10', 'AMC15'], ['AMM10', 'AMM15'],
    ['AMW10', 'AMW15'], ['ANG10', 'ANG15']]

pro_4 = [['O13', 'T13', 'O18', 'T18'], ['Y13', 'AD13', 'Y18', 'AD18'],
         ['AI13', 'AN13', 'AI18', 'AN18'], ['AS13', 'AX13', 'AS18', 'AX18'],
         ['BC13', 'BH13', 'BC18', 'BH18'], ['BM13', 'BR13', 'BM18', 'BR18'],
         ['BW13', 'CB13', 'BW18', 'CB18'],
         ['CG13', 'CL13', 'CG18', 'CL18'], ['CQ13', 'CV13', 'CQ18', 'CV18'],
         ['DA13', 'DF13', 'DA18', 'DF18'], ['DK13', 'DP13', 'DK18', 'DP18'],
         ['DU13', 'DZ13', 'DU18', 'DZ18'], ['EE13', 'EJ13', 'EE18', 'EJ18'],
         ['EO13', 'ET13', 'EO18', 'ET18'], ['EY13', 'FD13', 'EY18', 'FD18'],
         ['FI13', 'FN13', 'FI18', 'FN18'], ['FS13', 'FX13', 'FS18', 'FX18'],
         ['GC13', 'GH13', 'GC18', 'GH18'], ['GM13', 'GR13', 'GM18', 'GR18'],
         ['GW13', 'HB13', 'GW18', 'HB18'], ['HG13', 'HL13', 'HG18', 'HL18'],
         ['HQ13', 'HV13', 'HQ18', 'HV18'], ['IA13', 'IF13', 'IA18', 'IF18'],
         ['IK13', 'IP13', 'IK18', 'IP18'], ['IU13', 'IZ13', 'IU18', 'IZ18'],
         ['JE13', 'JJ13', 'JE18', 'JJ18'], ['JO13', 'JT13', 'JO18', 'JT18'],
         ['JY13', 'KD13', 'KY18', 'KD18'], ['KI13', 'KN13', 'KI18', 'KN18'],
         ['KS13', 'KX13', 'KS18', 'KX18'], ['LC13', 'LH13', 'LC18', 'LH18'],
         ['LM13', 'LR13', 'LM18', 'LR18'], ['LW13', 'MB13', 'LW18', 'MB18'],
         ['MG13', 'ML13', 'MG18', 'ML18'], ['MQ13', 'MV13', 'MQ18', 'MV18'],
         ['NA13', 'NF13', 'NA18', 'NF18'], ['NK13', 'NP13', 'NK18', 'NP18'],
         ['NU13', 'NZ13', 'NU18', 'NZ18'], ['OE13', 'OJ13', 'OE18', 'OJ18'],
         ['OO13', 'OT13', 'OO18', 'OT18'], ['OY13', 'PD13', 'OY18', 'PD18'],
         ['PI13', 'PN13', 'PI18', 'PN18'], ['PS13', 'PX13', 'PS18', 'PX18'],
         ['QC13', 'QH13', 'QC18', 'QH18'], ['QM13', 'QR13', 'QM18', 'QR18'],
         ['QW13', 'RB13', 'QW18', 'RB18'], ['RG13', 'RL13', 'RG18', 'RL18'],
         ['RQ13', 'RV13', 'RQ18', 'RV18'], ['SA13', 'SF13', 'SA18', 'SF18'],
         ['SK13', 'SP13', 'SK18', 'SP18'], ['SU13', 'SZ13', 'SU18', 'SZ18'],
         ['TE13', 'TJ13', 'TE18', 'TJ18'], ['TO13', 'TT13', 'TO18', 'TT18'],
         ['TY13', 'UD13', 'TY18', 'UD18'], ['UI13', 'UN13', 'UI18', 'UN18'],
         ['US13', 'UX13', 'US18', 'UX18'], ['VC13', 'VH13', 'VC18', 'VH18'],
         ['VM13', 'VR13', 'VM18', 'VR18'], ['VW13', 'WB13', 'VW18', 'WB18'],
         ['WG13', 'WL13', 'WG18', 'WL18'], ['WQ13', 'WV13', 'WQ18', 'WV18'],
         ['XA13', 'XF13', 'XA18', 'XF18'], ['XK13', 'XP13', 'XK18', 'XP18'],
         ['XU13', 'XZ13', 'XU18', 'XZ18'], ['YE13', 'YJ13', 'YE18', 'YJ18'],
         ['YO13', 'YT13', 'YO18', 'YT18'], ['YY13', 'ZD13', 'YY18', 'ZD18'],
         ['ZI13', 'ZN13', 'ZI18', 'ZN18'], ['ZS13', 'ZX13', 'ZS18', 'ZX18']]

pro_3 = [['O13', 'O18', 'T18'], ['Y13', 'Y18', 'AD18'],
         ['AI13', 'AI18', 'AN18'], ['AS13', 'AS18', 'AX18'],
         ['BC13', 'BC18', 'BH18'], ['BM13', 'BM18', 'BR18'],
         ['BW13', 'BW18', 'CB18'],
         ['CG13', 'CG18', 'CL18'], ['CQ13', 'CQ18', 'CV18'],
         ['DA13', 'DA18', 'DF18'], ['DK13', 'DK18', 'DP18'],
         ['DU13', 'DU18', 'DZ18'], ['EE13', 'EE18', 'EJ18'],
         ['EO13', 'EO18', 'ET18'], ['EY13', 'EY18', 'FD18'],
         ['FI13', 'FI18', 'FN18'], ['FS13', 'FS18', 'FX18'],
         ['GC13', 'GC18', 'GH18'], ['GM13', 'GM18', 'GR18'],
         ['GW13', 'GW18', 'HB18'], ['HG13', 'HG18', 'HL18'],
         ['HQ13', 'HQ18', 'HV18'], ['IA13', 'IA18', 'IF18'],
         ['IK13', 'IK18', 'IP18'], ['IU13', 'IU18', 'IZ18'],
         ['JE13', 'JE18', 'JJ18'], ['JO13', 'JO18', 'JT18'],
         ['JY13', 'KY18', 'KD18'], ['KI13', 'KI18', 'KN18'],
         ['KS13', 'KS18', 'KX18'], ['LC13', 'LC18', 'LH18'],
         ['LM13', 'LM18', 'LR18'], ['LW13', 'LW18', 'MB18'],
         ['MG13', 'MG18', 'ML18'], ['MQ13', 'MQ18', 'MV18'],
         ['NA13', 'NA18', 'NF18'], ['NK13', 'NK18', 'NP18'],
         ['NU13', 'NU18', 'NZ18'], ['OE13', 'OE18', 'OJ18'],
         ['OO13', 'OO18', 'OT18'], ['OY13', 'OY18', 'PD18'],
         ['PI13', 'PI18', 'PN18'], ['PS13', 'PS18', 'PX18'],
         ['QC13', 'QC18', 'QH18'], ['QM13', 'QM18', 'QR18'],
         ['QW13', 'QW18', 'RB18'], ['RG13', 'RG18', 'RL18'],
         ['RQ13', 'RQ18', 'RV18'], ['SA13', 'SA18', 'SF18'],
         ['SK13', 'SK18', 'SP18'], ['SU13', 'SU18', 'SZ18'],
         ['TE13', 'TE18', 'TJ18'], ['TO13', 'TO18', 'TT18'],
         ['TY13', 'TY18', 'UD18'], ['UI13', 'UI18', 'UN18'],
         ['US13', 'US18', 'UX18'], ['VC13', 'VC18', 'VH18'],
         ['VM13', 'VM18', 'VR18'], ['VW13', 'VW18', 'WB18'],
         ['WG13', 'WG18', 'WL18'], ['WQ13', 'WQ18', 'WV18'],
         ['XA13', 'XA18', 'XF18'], ['XK13', 'XK18', 'XP18'],
         ['XU13', 'XU18', 'XZ18'], ['YE13', 'YE18', 'YJ18'],
         ['YO13', 'YO18', 'YT18'], ['YY13', 'YY18', 'ZD18'],
         ['ZI13', 'ZI18', 'ZN18'], ['ZS13', 'ZS18', 'ZX18']]

pro_2 = [['O13', 'T13'], ['Y13', 'AD13'], ['AI13', 'AN13'], ['AS13', 'AX13'],
         ['BC13', 'BH13'], ['BM13', 'BR13'], ['BW13', 'CB13'],
         ['CG13', 'CL13'], ['CQ13', 'CV13'], ['DA13', 'DF13'], ['DK13', 'DP13'],
         ['DU13', 'DZ13'], ['EE13', 'EJ13'],
         ['EO13', 'ET13'], ['EY13', 'FD13'], ['FI13', 'FN13'], ['FS13', 'FX13'],
         ['GC13', 'GH13'], ['GM13', 'GR13'],
         ['GW13', 'HB13'], ['HG13', 'HL13'], ['HQ13', 'HV13'], ['IA13', 'IF13'],
         ['IK13', 'IP13'], ['IU13', 'IZ13'],
         ['JE13', 'JJ13'], ['JO13', 'JT13'], ['JY13', 'KD13'], ['KI13', 'KN13'],
         ['KS13', 'KX13'], ['LC13', 'LH13'],
         ['LM13', 'LR13'], ['LW13', 'MB13'], ['MG13', 'ML13'], ['MQ13', 'MV13'],
         ['NA13', 'NF13'], ['NK13', 'NP13'],
         ['NU13', 'NZ13'], ['OE13', 'OJ13'], ['OO13', 'OT13'], ['OY13', 'PD13'],
         ['PI13', 'PN13'], ['PS13', 'PX13'],
         ['QC13', 'QH13'], ['QM13', 'QR13'], ['QW13', 'RB13'], ['RG13', 'RL13'],
         ['RQ13', 'RV13'], ['SA13', 'SF13'],
         ['SK13', 'SP13'], ['SU13', 'SZ13'], ['TE13', 'TJ13'], ['TO13', 'TT13'],
         ['TY13', 'UD13'], ['UI13', 'UN13'],
         ['US13', 'UX13'], ['VC13', 'VH13'], ['VM13', 'VR13'], ['VW13', 'WB13'],
         ['WG13', 'WL13'], ['WQ13', 'WV13'],
         ['XA13', 'XF13'], ['XK13', 'XP13'], ['XU13', 'XZ13'], ['YE13', 'YJ13'],
         ['YO13', 'YT13'], ['YY13', 'ZD13'],
         ['ZI13', 'ZN13'], ['ZS13', 'ZX13']]

pro_2_2 = [['Y13', 'AD13'], ['AI13', 'AN13'], ['AS13', 'AX13'],
           ['BC13', 'BH13'], ['BM13', 'BR13'], ['BW13', 'CB13'],
           ['CG13', 'CL13'], ['CQ13', 'CV13'], ['DA13', 'DF13'],
           ['DK13', 'DP13'], ['DU13', 'DZ13'], ['EE13', 'EJ13'],
           ['EO13', 'ET13'], ['EY13', 'FD13'], ['FI13', 'FN13'],
           ['FS13', 'FX13'], ['GC13', 'GH13'], ['GM13', 'GR13'],
           ['GW13', 'HB13'], ['HG13', 'HL13'], ['HQ13', 'HV13'],
           ['IA13', 'IF13'], ['IK13', 'IP13'], ['IU13', 'IZ13'],
           ['JE13', 'JJ13'], ['JO13', 'JT13'], ['JY13', 'KD13'],
           ['KI13', 'KN13'], ['KS13', 'KX13'], ['LC13', 'LH13'],
           ['LM13', 'LR13'], ['LW13', 'MB13'], ['MG13', 'ML13'],
           ['MQ13', 'MV13'], ['NA13', 'NF13'], ['NK13', 'NP13'],
           ['NU13', 'NZ13'], ['OE13', 'OJ13'], ['OO13', 'OT13'],
           ['OY13', 'PD13'], ['PI13', 'PN13'], ['PS13', 'PX13'],
           ['QC13', 'QH13'], ['QM13', 'QR13'], ['QW13', 'RB13'],
           ['RG13', 'RL13'], ['RQ13', 'RV13'], ['SA13', 'SF13'],
           ['SK13', 'SP13'], ['SU13', 'SZ13'], ['TE13', 'TJ13'],
           ['TO13', 'TT13'], ['TY13', 'UD13'], ['UI13', 'UN13'],
           ['US13', 'UX13'], ['VC13', 'VH13'], ['VM13', 'VR13'],
           ['VW13', 'WB13'], ['WG13', 'WL13'], ['WQ13', 'WV13'],
           ['XA13', 'XF13'], ['XK13', 'XP13'], ['XU13', 'XZ13'],
           ['YE13', 'YJ13'], ['YO13', 'YT13'], ['YY13', 'ZD13'],
           ['ZI13', 'ZN13'], ['ZS13', 'ZX13']]

pro_3_2 = [['Y13', 'Y18', 'AD18'], ['AI13', 'AI18', 'AN18'],
           ['AS13', 'AS18', 'AX18'], ['BC13', 'BC18', 'BH18'],
           ['BM13', 'BM18', 'BR18'], ['BW13', 'BW18', 'CB18'],
           ['CG13', 'CG18', 'CL18'], ['CQ13', 'CQ18', 'CV18'],
           ['DA13', 'DA18', 'DF18'], ['DK13', 'DK18', 'DP18'],
           ['DU13', 'DU18', 'DZ18'], ['EE13', 'EE18', 'EJ18'],
           ['EO13', 'EO18', 'ET18'], ['EY13', 'EY18', 'FD18'],
           ['FI13', 'FI18', 'FN18'], ['FS13', 'FS18', 'FX18'],
           ['GC13', 'GC18', 'GH18'], ['GM13', 'GM18', 'GR18'],
           ['GW13', 'GW18', 'HB18'], ['HG13', 'HG18', 'HL18'],
           ['HQ13', 'HQ18', 'HV18'], ['IA13', 'IA18', 'IF18'],
           ['IK13', 'IK18', 'IP18'], ['IU13', 'IU18', 'IZ18'],
           ['JE13', 'JE18', 'JJ18'], ['JO13', 'JO18', 'JT18'],
           ['JY13', 'KY18', 'KD18'], ['KI13', 'KI18', 'KN18'],
           ['KS13', 'KS18', 'KX18'], ['LC13', 'LC18', 'LH18'],
           ['LM13', 'LM18', 'LR18'], ['LW13', 'LW18', 'MB18'],
           ['MG13', 'MG18', 'ML18'], ['MQ13', 'MQ18', 'MV18'],
           ['NA13', 'NA18', 'NF18'], ['NK13', 'NK18', 'NP18'],
           ['NU13', 'NU18', 'NZ18'], ['OE13', 'OE18', 'OJ18'],
           ['OO13', 'OO18', 'OT18'], ['OY13', 'OY18', 'PD18'],
           ['PI13', 'PI18', 'PN18'], ['PS13', 'PS18', 'PX18'],
           ['QC13', 'QC18', 'QH18'], ['QM13', 'QM18', 'QR18'],
           ['QW13', 'QW18', 'RB18'], ['RG13', 'RG18', 'RL18'],
           ['RQ13', 'RQ18', 'RV18'], ['SA13', 'SA18', 'SF18'],
           ['SK13', 'SK18', 'SP18'], ['SU13', 'SU18', 'SZ18'],
           ['TE13', 'TE18', 'TJ18'], ['TO13', 'TO18', 'TT18'],
           ['TY13', 'TY18', 'UD18'], ['UI13', 'UI18', 'UN18'],
           ['US13', 'US18', 'UX18'], ['VC13', 'VC18', 'VH18'],
           ['VM13', 'VM18', 'VR18'], ['VW13', 'VW18', 'WB18'],
           ['WG13', 'WG18', 'WL18'], ['WQ13', 'WQ18', 'WV18'],
           ['XA13', 'XA18', 'XF18'], ['XK13', 'XK18', 'XP18'],
           ['XU13', 'XU18', 'XZ18'], ['YE13', 'YE18', 'YJ18'],
           ['YO13', 'YO18', 'YT18'], ['YY13', 'YY18', 'ZD18'],
           ['ZI13', 'ZI18', 'ZN18'], ['ZS13', 'ZS18', 'ZX18']]

pro_4_2 = [['Y13', 'AD13', 'Y18', 'AD18'], ['AI13', 'AN13', 'AI18', 'AN18'],
           ['AS13', 'AX13', 'AS18', 'AX18'], ['BC13', 'BH13', 'BC18', 'BH18'],
           ['BM13', 'BR13', 'BM18', 'BR18'], ['BW13', 'CB13', 'BW18', 'CB18'],
           ['CG13', 'CL13', 'CG18', 'CL18'], ['CQ13', 'CV13', 'CQ18', 'CV18'],
           ['DA13', 'DF13', 'DA18', 'DF18'], ['DK13', 'DP13', 'DK18', 'DP18'],
           ['DU13', 'DZ13', 'DU18', 'DZ18'], ['EE13', 'EJ13', 'EE18', 'EJ18'],
           ['EO13', 'ET13', 'EO18', 'ET18'], ['EY13', 'FD13', 'EY18', 'FD18'],
           ['FI13', 'FN13', 'FI18', 'FN18'], ['FS13', 'FX13', 'FS18', 'FX18'],
           ['GC13', 'GH13', 'GC18', 'GH18'], ['GM13', 'GR13', 'GM18', 'GR18'],
           ['GW13', 'HB13', 'GW18', 'HB18'], ['HG13', 'HL13', 'HG18', 'HL18'],
           ['HQ13', 'HV13', 'HQ18', 'HV18'], ['IA13', 'IF13', 'IA18', 'IF18'],
           ['IK13', 'IP13', 'IK18', 'IP18'], ['IU13', 'IZ13', 'IU18', 'IZ18'],
           ['JE13', 'JJ13', 'JE18', 'JJ18'], ['JO13', 'JT13', 'JO18', 'JT18'],
           ['JY13', 'KD13', 'KY18', 'KD18'], ['KI13', 'KN13', 'KI18', 'KN18'],
           ['KS13', 'KX13', 'KS18', 'KX18'], ['LC13', 'LH13', 'LC18', 'LH18'],
           ['LM13', 'LR13', 'LM18', 'LR18'], ['LW13', 'MB13', 'LW18', 'MB18'],
           ['MG13', 'ML13', 'MG18', 'ML18'], ['MQ13', 'MV13', 'MQ18', 'MV18'],
           ['NA13', 'NF13', 'NA18', 'NF18'], ['NK13', 'NP13', 'NK18', 'NP18'],
           ['NU13', 'NZ13', 'NU18', 'NZ18'], ['OE13', 'OJ13', 'OE18', 'OJ18'],
           ['OO13', 'OT13', 'OO18', 'OT18'], ['OY13', 'PD13', 'OY18', 'PD18'],
           ['PI13', 'PN13', 'PI18', 'PN18'], ['PS13', 'PX13', 'PS18', 'PX18'],
           ['QC13', 'QH13', 'QC18', 'QH18'], ['QM13', 'QR13', 'QM18', 'QR18'],
           ['QW13', 'RB13', 'QW18', 'RB18'], ['RG13', 'RL13', 'RG18', 'RL18'],
           ['RQ13', 'RV13', 'RQ18', 'RV18'], ['SA13', 'SF13', 'SA18', 'SF18'],
           ['SK13', 'SP13', 'SK18', 'SP18'], ['SU13', 'SZ13', 'SU18', 'SZ18'],
           ['TE13', 'TJ13', 'TE18', 'TJ18'], ['TO13', 'TT13', 'TO18', 'TT18'],
           ['TY13', 'UD13', 'TY18', 'UD18'], ['UI13', 'UN13', 'UI18', 'UN18'],
           ['US13', 'UX13', 'US18', 'UX18'], ['VC13', 'VH13', 'VC18', 'VH18'],
           ['VM13', 'VR13', 'VM18', 'VR18'], ['VW13', 'WB13', 'VW18', 'WB18'],
           ['WG13', 'WL13', 'WG18', 'WL18'], ['WQ13', 'WV13', 'WQ18', 'WV18'],
           ['XA13', 'XF13', 'XA18', 'XF18'], ['XK13', 'XP13', 'XK18', 'XP18'],
           ['XU13', 'XZ13', 'XU18', 'XZ18'], ['YE13', 'YJ13', 'YE18', 'YJ18'],
           ['YO13', 'YT13', 'YO18', 'YT18'], ['YY13', 'ZD13', 'YY18', 'ZD18'],
           ['ZI13', 'ZN13', 'ZI18', 'ZN18'], ['ZS13', 'ZX13', 'ZS18', 'ZX18']]

pro_2_3 = [['AI13', 'AN13'], ['AS13', 'AX13'], ['BC13', 'BH13'],
           ['BM13', 'BR13'], ['BW13', 'CB13'],
           ['CG13', 'CL13'], ['CQ13', 'CV13'], ['DA13', 'DF13'],
           ['DK13', 'DP13'], ['DU13', 'DZ13'], ['EE13', 'EJ13'],
           ['EO13', 'ET13'], ['EY13', 'FD13'], ['FI13', 'FN13'],
           ['FS13', 'FX13'], ['GC13', 'GH13'], ['GM13', 'GR13'],
           ['GW13', 'HB13'], ['HG13', 'HL13'], ['HQ13', 'HV13'],
           ['IA13', 'IF13'], ['IK13', 'IP13'], ['IU13', 'IZ13'],
           ['JE13', 'JJ13'], ['JO13', 'JT13'], ['JY13', 'KD13'],
           ['KI13', 'KN13'], ['KS13', 'KX13'], ['LC13', 'LH13'],
           ['LM13', 'LR13'], ['LW13', 'MB13'], ['MG13', 'ML13'],
           ['MQ13', 'MV13'], ['NA13', 'NF13'], ['NK13', 'NP13'],
           ['NU13', 'NZ13'], ['OE13', 'OJ13'], ['OO13', 'OT13'],
           ['OY13', 'PD13'], ['PI13', 'PN13'], ['PS13', 'PX13'],
           ['QC13', 'QH13'], ['QM13', 'QR13'], ['QW13', 'RB13'],
           ['RG13', 'RL13'], ['RQ13', 'RV13'], ['SA13', 'SF13'],
           ['SK13', 'SP13'], ['SU13', 'SZ13'], ['TE13', 'TJ13'],
           ['TO13', 'TT13'], ['TY13', 'UD13'], ['UI13', 'UN13'],
           ['US13', 'UX13'], ['VC13', 'VH13'], ['VM13', 'VR13'],
           ['VW13', 'WB13'], ['WG13', 'WL13'], ['WQ13', 'WV13'],
           ['XA13', 'XF13'], ['XK13', 'XP13'], ['XU13', 'XZ13'],
           ['YE13', 'YJ13'], ['YO13', 'YT13'], ['YY13', 'ZD13'],
           ['ZI13', 'ZN13'], ['ZS13', 'ZX13'], ['AAC13', 'AAH13']]

pro_3_3 = [['AI13', 'AI18', 'AN18'], ['AS13', 'AS18', 'AX18'],
           ['BC13', 'BC18', 'BH18'], ['BM13', 'BM18', 'BR18'],
           ['BW13', 'BW18', 'CB18'],
           ['CG13', 'CG18', 'CL18'], ['CQ13', 'CQ18', 'CV18'],
           ['DA13', 'DA18', 'DF18'], ['DK13', 'DK18', 'DP18'],
           ['DU13', 'DU18', 'DZ18'], ['EE13', 'EE18', 'EJ18'],
           ['EO13', 'EO18', 'ET18'], ['EY13', 'EY18', 'FD18'],
           ['FI13', 'FI18', 'FN18'], ['FS13', 'FS18', 'FX18'],
           ['GC13', 'GC18', 'GH18'], ['GM13', 'GM18', 'GR18'],
           ['GW13', 'GW18', 'HB18'], ['HG13', 'HG18', 'HL18'],
           ['HQ13', 'HQ18', 'HV18'], ['IA13', 'IA18', 'IF18'],
           ['IK13', 'IK18', 'IP18'], ['IU13', 'IU18', 'IZ18'],
           ['JE13', 'JE18', 'JJ18'], ['JO13', 'JO18', 'JT18'],
           ['JY13', 'KY18', 'KD18'], ['KI13', 'KI18', 'KN18'],
           ['KS13', 'KS18', 'KX18'], ['LC13', 'LC18', 'LH18'],
           ['LM13', 'LM18', 'LR18'], ['LW13', 'LW18', 'MB18'],
           ['MG13', 'MG18', 'ML18'], ['MQ13', 'MQ18', 'MV18'],
           ['NA13', 'NA18', 'NF18'], ['NK13', 'NK18', 'NP18'],
           ['NU13', 'NU18', 'NZ18'], ['OE13', 'OE18', 'OJ18'],
           ['OO13', 'OO18', 'OT18'], ['OY13', 'OY18', 'PD18'],
           ['PI13', 'PI18', 'PN18'], ['PS13', 'PS18', 'PX18'],
           ['QC13', 'QC18', 'QH18'], ['QM13', 'QM18', 'QR18'],
           ['QW13', 'QW18', 'RB18'], ['RG13', 'RG18', 'RL18'],
           ['RQ13', 'RQ18', 'RV18'], ['SA13', 'SA18', 'SF18'],
           ['SK13', 'SK18', 'SP18'], ['SU13', 'SU18', 'SZ18'],
           ['TE13', 'TE18', 'TJ18'], ['TO13', 'TO18', 'TT18'],
           ['TY13', 'TY18', 'UD18'], ['UI13', 'UI18', 'UN18'],
           ['US13', 'US18', 'UX18'], ['VC13', 'VC18', 'VH18'],
           ['VM13', 'VM18', 'VR18'], ['VW13', 'VW18', 'WB18'],
           ['WG13', 'WG18', 'WL18'], ['WQ13', 'WQ18', 'WV18'],
           ['XA13', 'XA18', 'XF18'], ['XK13', 'XK18', 'XP18'],
           ['XU13', 'XU18', 'XZ18'], ['YE13', 'YE18', 'YJ18'],
           ['YO13', 'YO18', 'YT18'], ['YY13', 'YY18', 'ZD18'],
           ['ZI13', 'ZI18', 'ZN18'], ['ZS13', 'ZS18', 'ZX18'],
           ['AAC13', 'AAC18', 'AAH18']]

pro_4_3 = [['AI13', 'AN13', 'AI18', 'AN18'], ['AS13', 'AX13', 'AS18', 'AX18'],
           ['BC13', 'BH13', 'BC18', 'BH18'], ['BM13', 'BR13', 'BM18', 'BR18'],
           ['BW13', 'CB13', 'BW18', 'CB18'],
           ['CG13', 'CL13', 'CG18', 'CL18'], ['CQ13', 'CV13', 'CQ18', 'CV18'],
           ['DA13', 'DF13', 'DA18', 'DF18'], ['DK13', 'DP13', 'DK18', 'DP18'],
           ['DU13', 'DZ13', 'DU18', 'DZ18'], ['EE13', 'EJ13', 'EE18', 'EJ18'],
           ['EO13', 'ET13', 'EO18', 'ET18'], ['EY13', 'FD13', 'EY18', 'FD18'],
           ['FI13', 'FN13', 'FI18', 'FN18'], ['FS13', 'FX13', 'FS18', 'FX18'],
           ['GC13', 'GH13', 'GC18', 'GH18'], ['GM13', 'GR13', 'GM18', 'GR18'],
           ['GW13', 'HB13', 'GW18', 'HB18'], ['HG13', 'HL13', 'HG18', 'HL18'],
           ['HQ13', 'HV13', 'HQ18', 'HV18'], ['IA13', 'IF13', 'IA18', 'IF18'],
           ['IK13', 'IP13', 'IK18', 'IP18'], ['IU13', 'IZ13', 'IU18', 'IZ18'],
           ['JE13', 'JJ13', 'JE18', 'JJ18'], ['JO13', 'JT13', 'JO18', 'JT18'],
           ['JY13', 'KD13', 'KY18', 'KD18'], ['KI13', 'KN13', 'KI18', 'KN18'],
           ['KS13', 'KX13', 'KS18', 'KX18'], ['LC13', 'LH13', 'LC18', 'LH18'],
           ['LM13', 'LR13', 'LM18', 'LR18'], ['LW13', 'MB13', 'LW18', 'MB18'],
           ['MG13', 'ML13', 'MG18', 'ML18'], ['MQ13', 'MV13', 'MQ18', 'MV18'],
           ['NA13', 'NF13', 'NA18', 'NF18'], ['NK13', 'NP13', 'NK18', 'NP18'],
           ['NU13', 'NZ13', 'NU18', 'NZ18'], ['OE13', 'OJ13', 'OE18', 'OJ18'],
           ['OO13', 'OT13', 'OO18', 'OT18'], ['OY13', 'PD13', 'OY18', 'PD18'],
           ['PI13', 'PN13', 'PI18', 'PN18'], ['PS13', 'PX13', 'PS18', 'PX18'],
           ['QC13', 'QH13', 'QC18', 'QH18'], ['QM13', 'QR13', 'QM18', 'QR18'],
           ['QW13', 'RB13', 'QW18', 'RB18'], ['RG13', 'RL13', 'RG18', 'RL18'],
           ['RQ13', 'RV13', 'RQ18', 'RV18'], ['SA13', 'SF13', 'SA18', 'SF18'],
           ['SK13', 'SP13', 'SK18', 'SP18'], ['SU13', 'SZ13', 'SU18', 'SZ18'],
           ['TE13', 'TJ13', 'TE18', 'TJ18'], ['TO13', 'TT13', 'TO18', 'TT18'],
           ['TY13', 'UD13', 'TY18', 'UD18'], ['UI13', 'UN13', 'UI18', 'UN18'],
           ['US13', 'UX13', 'US18', 'UX18'], ['VC13', 'VH13', 'VC18', 'VH18'],
           ['VM13', 'VR13', 'VM18', 'VR18'], ['VW13', 'WB13', 'VW18', 'WB18'],
           ['WG13', 'WL13', 'WG18', 'WL18'], ['WQ13', 'WV13', 'WQ18', 'WV18'],
           ['XA13', 'XF13', 'XA18', 'XF18'], ['XK13', 'XP13', 'XK18', 'XP18'],
           ['XU13', 'XZ13', 'XU18', 'XZ18'], ['YE13', 'YJ13', 'YE18', 'YJ18'],
           ['YO13', 'YT13', 'YO18', 'YT18'], ['YY13', 'ZD13', 'YY18', 'ZD18'],
           ['ZI13', 'ZN13', 'ZI18', 'ZN18'], ['ZS13', 'ZX13', 'ZS18', 'ZX18'],
           ['AAC13', 'AAH13', 'AAC18', 'AAH18']]

pro_2_4 = [['AS13', 'AX13'], ['BC13', 'BH13'], ['BM13', 'BR13'],
           ['BW13', 'CB13'],
           ['CG13', 'CL13'], ['CQ13', 'CV13'], ['DA13', 'DF13'],
           ['DK13', 'DP13'], ['DU13', 'DZ13'], ['EE13', 'EJ13'],
           ['EO13', 'ET13'], ['EY13', 'FD13'], ['FI13', 'FN13'],
           ['FS13', 'FX13'], ['GC13', 'GH13'], ['GM13', 'GR13'],
           ['GW13', 'HB13'], ['HG13', 'HL13'], ['HQ13', 'HV13'],
           ['IA13', 'IF13'], ['IK13', 'IP13'], ['IU13', 'IZ13'],
           ['JE13', 'JJ13'], ['JO13', 'JT13'], ['JY13', 'KD13'],
           ['KI13', 'KN13'], ['KS13', 'KX13'], ['LC13', 'LH13'],
           ['LM13', 'LR13'], ['LW13', 'MB13'], ['MG13', 'ML13'],
           ['MQ13', 'MV13'], ['NA13', 'NF13'], ['NK13', 'NP13'],
           ['NU13', 'NZ13'], ['OE13', 'OJ13'], ['OO13', 'OT13'],
           ['OY13', 'PD13'], ['PI13', 'PN13'], ['PS13', 'PX13'],
           ['QC13', 'QH13'], ['QM13', 'QR13'], ['QW13', 'RB13'],
           ['RG13', 'RL13'], ['RQ13', 'RV13'], ['SA13', 'SF13'],
           ['SK13', 'SP13'], ['SU13', 'SZ13'], ['TE13', 'TJ13'],
           ['TO13', 'TT13'], ['TY13', 'UD13'], ['UI13', 'UN13'],
           ['US13', 'UX13'], ['VC13', 'VH13'], ['VM13', 'VR13'],
           ['VW13', 'WB13'], ['WG13', 'WL13'], ['WQ13', 'WV13'],
           ['XA13', 'XF13'], ['XK13', 'XP13'], ['XU13', 'XZ13'],
           ['YE13', 'YJ13'], ['YO13', 'YT13'], ['YY13', 'ZD13'],
           ['ZI13', 'ZN13'], ['ZS13', 'ZX13'], ['AAC13', 'AAH13'],
           ['AAM13', 'AAR13']]

pro_3_4 = [['AS13', 'AS18', 'AX18'], ['BC13', 'BC18', 'BH18'],
           ['BM13', 'BM18', 'BR18'], ['BW13', 'BW18', 'CB18'],
           ['CG13', 'CG18', 'CL18'], ['CQ13', 'CQ18', 'CV18'],
           ['DA13', 'DA18', 'DF18'], ['DK13', 'DK18', 'DP18'],
           ['DU13', 'DU18', 'DZ18'], ['EE13', 'EE18', 'EJ18'],
           ['EO13', 'EO18', 'ET18'], ['EY13', 'EY18', 'FD18'],
           ['FI13', 'FI18', 'FN18'], ['FS13', 'FS18', 'FX18'],
           ['GC13', 'GC18', 'GH18'], ['GM13', 'GM18', 'GR18'],
           ['GW13', 'GW18', 'HB18'], ['HG13', 'HG18', 'HL18'],
           ['HQ13', 'HQ18', 'HV18'], ['IA13', 'IA18', 'IF18'],
           ['IK13', 'IK18', 'IP18'], ['IU13', 'IU18', 'IZ18'],
           ['JE13', 'JE18', 'JJ18'], ['JO13', 'JO18', 'JT18'],
           ['JY13', 'KY18', 'KD18'], ['KI13', 'KI18', 'KN18'],
           ['KS13', 'KS18', 'KX18'], ['LC13', 'LC18', 'LH18'],
           ['LM13', 'LM18', 'LR18'], ['LW13', 'LW18', 'MB18'],
           ['MG13', 'MG18', 'ML18'], ['MQ13', 'MQ18', 'MV18'],
           ['NA13', 'NA18', 'NF18'], ['NK13', 'NK18', 'NP18'],
           ['NU13', 'NU18', 'NZ18'], ['OE13', 'OE18', 'OJ18'],
           ['OO13', 'OO18', 'OT18'], ['OY13', 'OY18', 'PD18'],
           ['PI13', 'PI18', 'PN18'], ['PS13', 'PS18', 'PX18'],
           ['QC13', 'QC18', 'QH18'], ['QM13', 'QM18', 'QR18'],
           ['QW13', 'QW18', 'RB18'], ['RG13', 'RG18', 'RL18'],
           ['RQ13', 'RQ18', 'RV18'], ['SA13', 'SA18', 'SF18'],
           ['SK13', 'SK18', 'SP18'], ['SU13', 'SU18', 'SZ18'],
           ['TE13', 'TE18', 'TJ18'], ['TO13', 'TO18', 'TT18'],
           ['TY13', 'TY18', 'UD18'], ['UI13', 'UI18', 'UN18'],
           ['US13', 'US18', 'UX18'], ['VC13', 'VC18', 'VH18'],
           ['VM13', 'VM18', 'VR18'], ['VW13', 'VW18', 'WB18'],
           ['WG13', 'WG18', 'WL18'], ['WQ13', 'WQ18', 'WV18'],
           ['XA13', 'XA18', 'XF18'], ['XK13', 'XK18', 'XP18'],
           ['XU13', 'XU18', 'XZ18'], ['YE13', 'YE18', 'YJ18'],
           ['YO13', 'YO18', 'YT18'], ['YY13', 'YY18', 'ZD18'],
           ['ZI13', 'ZI18', 'ZN18'], ['ZS13', 'ZS18', 'ZX18'],
           ['AAC13', 'AAC18', 'AAH18'], ['AAM13', 'AAM18', 'AAR18']]

pro_4_4 = [['AS13', 'AX13', 'AS18', 'AX18'], ['BC13', 'BH13', 'BC18', 'BH18'],
           ['BM13', 'BR13', 'BM18', 'BR18'], ['BW13', 'CB13', 'BW18', 'CB18'],
           ['CG13', 'CL13', 'CG18', 'CL18'], ['CQ13', 'CV13', 'CQ18', 'CV18'],
           ['DA13', 'DF13', 'DA18', 'DF18'], ['DK13', 'DP13', 'DK18', 'DP18'],
           ['DU13', 'DZ13', 'DU18', 'DZ18'], ['EE13', 'EJ13', 'EE18', 'EJ18'],
           ['EO13', 'ET13', 'EO18', 'ET18'], ['EY13', 'FD13', 'EY18', 'FD18'],
           ['FI13', 'FN13', 'FI18', 'FN18'], ['FS13', 'FX13', 'FS18', 'FX18'],
           ['GC13', 'GH13', 'GC18', 'GH18'], ['GM13', 'GR13', 'GM18', 'GR18'],
           ['GW13', 'HB13', 'GW18', 'HB18'], ['HG13', 'HL13', 'HG18', 'HL18'],
           ['HQ13', 'HV13', 'HQ18', 'HV18'], ['IA13', 'IF13', 'IA18', 'IF18'],
           ['IK13', 'IP13', 'IK18', 'IP18'], ['IU13', 'IZ13', 'IU18', 'IZ18'],
           ['JE13', 'JJ13', 'JE18', 'JJ18'], ['JO13', 'JT13', 'JO18', 'JT18'],
           ['JY13', 'KD13', 'KY18', 'KD18'], ['KI13', 'KN13', 'KI18', 'KN18'],
           ['KS13', 'KX13', 'KS18', 'KX18'], ['LC13', 'LH13', 'LC18', 'LH18'],
           ['LM13', 'LR13', 'LM18', 'LR18'], ['LW13', 'MB13', 'LW18', 'MB18'],
           ['MG13', 'ML13', 'MG18', 'ML18'], ['MQ13', 'MV13', 'MQ18', 'MV18'],
           ['NA13', 'NF13', 'NA18', 'NF18'], ['NK13', 'NP13', 'NK18', 'NP18'],
           ['NU13', 'NZ13', 'NU18', 'NZ18'], ['OE13', 'OJ13', 'OE18', 'OJ18'],
           ['OO13', 'OT13', 'OO18', 'OT18'], ['OY13', 'PD13', 'OY18', 'PD18'],
           ['PI13', 'PN13', 'PI18', 'PN18'], ['PS13', 'PX13', 'PS18', 'PX18'],
           ['QC13', 'QH13', 'QC18', 'QH18'], ['QM13', 'QR13', 'QM18', 'QR18'],
           ['QW13', 'RB13', 'QW18', 'RB18'], ['RG13', 'RL13', 'RG18', 'RL18'],
           ['RQ13', 'RV13', 'RQ18', 'RV18'], ['SA13', 'SF13', 'SA18', 'SF18'],
           ['SK13', 'SP13', 'SK18', 'SP18'], ['SU13', 'SZ13', 'SU18', 'SZ18'],
           ['TE13', 'TJ13', 'TE18', 'TJ18'], ['TO13', 'TT13', 'TO18', 'TT18'],
           ['TY13', 'UD13', 'TY18', 'UD18'], ['UI13', 'UN13', 'UI18', 'UN18'],
           ['US13', 'UX13', 'US18', 'UX18'], ['VC13', 'VH13', 'VC18', 'VH18'],
           ['VM13', 'VR13', 'VM18', 'VR18'], ['VW13', 'WB13', 'VW18', 'WB18'],
           ['WG13', 'WL13', 'WG18', 'WL18'], ['WQ13', 'WV13', 'WQ18', 'WV18'],
           ['XA13', 'XF13', 'XA18', 'XF18'], ['XK13', 'XP13', 'XK18', 'XP18'],
           ['XU13', 'XZ13', 'XU18', 'XZ18'], ['YE13', 'YJ13', 'YE18', 'YJ18'],
           ['YO13', 'YT13', 'YO18', 'YT18'], ['YY13', 'ZD13', 'YY18', 'ZD18'],
           ['ZI13', 'ZN13', 'ZI18', 'ZN18'], ['ZS13', 'ZX13', 'ZS18', 'ZX18'],
           ['AAC13', 'AAH13', 'AAC18', 'AAH18'],
           ['AAM13', 'AAR13', 'AAM18', 'AAR18']]

pro_2_5 = [['BC13', 'BH13'], ['BM13', 'BR13'], ['BW13', 'CB13'],
           ['CG13', 'CL13'], ['CQ13', 'CV13'], ['DA13', 'DF13'],
           ['DK13', 'DP13'], ['DU13', 'DZ13'], ['EE13', 'EJ13'],
           ['EO13', 'ET13'], ['EY13', 'FD13'], ['FI13', 'FN13'],
           ['FS13', 'FX13'], ['GC13', 'GH13'], ['GM13', 'GR13'],
           ['GW13', 'HB13'], ['HG13', 'HL13'], ['HQ13', 'HV13'],
           ['IA13', 'IF13'], ['IK13', 'IP13'], ['IU13', 'IZ13'],
           ['JE13', 'JJ13'], ['JO13', 'JT13'], ['JY13', 'KD13'],
           ['KI13', 'KN13'], ['KS13', 'KX13'], ['LC13', 'LH13'],
           ['LM13', 'LR13'], ['LW13', 'MB13'], ['MG13', 'ML13'],
           ['MQ13', 'MV13'], ['NA13', 'NF13'], ['NK13', 'NP13'],
           ['NU13', 'NZ13'], ['OE13', 'OJ13'], ['OO13', 'OT13'],
           ['OY13', 'PD13'], ['PI13', 'PN13'], ['PS13', 'PX13'],
           ['QC13', 'QH13'], ['QM13', 'QR13'], ['QW13', 'RB13'],
           ['RG13', 'RL13'], ['RQ13', 'RV13'], ['SA13', 'SF13'],
           ['SK13', 'SP13'], ['SU13', 'SZ13'], ['TE13', 'TJ13'],
           ['TO13', 'TT13'], ['TY13', 'UD13'], ['UI13', 'UN13'],
           ['US13', 'UX13'], ['VC13', 'VH13'], ['VM13', 'VR13'],
           ['VW13', 'WB13'], ['WG13', 'WL13'], ['WQ13', 'WV13'],
           ['XA13', 'XF13'], ['XK13', 'XP13'], ['XU13', 'XZ13'],
           ['YE13', 'YJ13'], ['YO13', 'YT13'], ['YY13', 'ZD13'],
           ['ZI13', 'ZN13'], ['ZS13', 'ZX13'], ['AAC13', 'AAH13'],
           ['AAM13', 'AAR13'], ['AAW13', 'ABB13']]

pro_3_5 = [['BC13', 'BC18', 'BH18'], ['BM13', 'BM18', 'BR18'],
           ['BW13', 'BW18', 'CB18'],
           ['CG13', 'CG18', 'CL18'], ['CQ13', 'CQ18', 'CV18'],
           ['DA13', 'DA18', 'DF18'], ['DK13', 'DK18', 'DP18'],
           ['DU13', 'DU18', 'DZ18'], ['EE13', 'EE18', 'EJ18'],
           ['EO13', 'EO18', 'ET18'], ['EY13', 'EY18', 'FD18'],
           ['FI13', 'FI18', 'FN18'], ['FS13', 'FS18', 'FX18'],
           ['GC13', 'GC18', 'GH18'], ['GM13', 'GM18', 'GR18'],
           ['GW13', 'GW18', 'HB18'], ['HG13', 'HG18', 'HL18'],
           ['HQ13', 'HQ18', 'HV18'], ['IA13', 'IA18', 'IF18'],
           ['IK13', 'IK18', 'IP18'], ['IU13', 'IU18', 'IZ18'],
           ['JE13', 'JE18', 'JJ18'], ['JO13', 'JO18', 'JT18'],
           ['JY13', 'KY18', 'KD18'], ['KI13', 'KI18', 'KN18'],
           ['KS13', 'KS18', 'KX18'], ['LC13', 'LC18', 'LH18'],
           ['LM13', 'LM18', 'LR18'], ['LW13', 'LW18', 'MB18'],
           ['MG13', 'MG18', 'ML18'], ['MQ13', 'MQ18', 'MV18'],
           ['NA13', 'NA18', 'NF18'], ['NK13', 'NK18', 'NP18'],
           ['NU13', 'NU18', 'NZ18'], ['OE13', 'OE18', 'OJ18'],
           ['OO13', 'OO18', 'OT18'], ['OY13', 'OY18', 'PD18'],
           ['PI13', 'PI18', 'PN18'], ['PS13', 'PS18', 'PX18'],
           ['QC13', 'QC18', 'QH18'], ['QM13', 'QM18', 'QR18'],
           ['QW13', 'QW18', 'RB18'], ['RG13', 'RG18', 'RL18'],
           ['RQ13', 'RQ18', 'RV18'], ['SA13', 'SA18', 'SF18'],
           ['SK13', 'SK18', 'SP18'], ['SU13', 'SU18', 'SZ18'],
           ['TE13', 'TE18', 'TJ18'], ['TO13', 'TO18', 'TT18'],
           ['TY13', 'TY18', 'UD18'], ['UI13', 'UI18', 'UN18'],
           ['US13', 'US18', 'UX18'], ['VC13', 'VC18', 'VH18'],
           ['VM13', 'VM18', 'VR18'], ['VW13', 'VW18', 'WB18'],
           ['WG13', 'WG18', 'WL18'], ['WQ13', 'WQ18', 'WV18'],
           ['XA13', 'XA18', 'XF18'], ['XK13', 'XK18', 'XP18'],
           ['XU13', 'XU18', 'XZ18'], ['YE13', 'YE18', 'YJ18'],
           ['YO13', 'YO18', 'YT18'], ['YY13', 'YY18', 'ZD18'],
           ['ZI13', 'ZI18', 'ZN18'], ['ZS13', 'ZS18', 'ZX18'],
           ['AAC13', 'AAC18', 'AAH18'], ['AAM13', 'AAM18', 'AAR18'],
           ['AAW13', 'AAW18', 'ABB18']]

pro_4_5 = [['BC13', 'BH13', 'BC18', 'BH18'], ['BM13', 'BR13', 'BM18', 'BR18'],
           ['BW13', 'CB13', 'BW18', 'CB18'],
           ['CG13', 'CL13', 'CG18', 'CL18'], ['CQ13', 'CV13', 'CQ18', 'CV18'],
           ['DA13', 'DF13', 'DA18', 'DF18'], ['DK13', 'DP13', 'DK18', 'DP18'],
           ['DU13', 'DZ13', 'DU18', 'DZ18'], ['EE13', 'EJ13', 'EE18', 'EJ18'],
           ['EO13', 'ET13', 'EO18', 'ET18'], ['EY13', 'FD13', 'EY18', 'FD18'],
           ['FI13', 'FN13', 'FI18', 'FN18'], ['FS13', 'FX13', 'FS18', 'FX18'],
           ['GC13', 'GH13', 'GC18', 'GH18'], ['GM13', 'GR13', 'GM18', 'GR18'],
           ['GW13', 'HB13', 'GW18', 'HB18'], ['HG13', 'HL13', 'HG18', 'HL18'],
           ['HQ13', 'HV13', 'HQ18', 'HV18'], ['IA13', 'IF13', 'IA18', 'IF18'],
           ['IK13', 'IP13', 'IK18', 'IP18'], ['IU13', 'IZ13', 'IU18', 'IZ18'],
           ['JE13', 'JJ13', 'JE18', 'JJ18'], ['JO13', 'JT13', 'JO18', 'JT18'],
           ['JY13', 'KD13', 'KY18', 'KD18'], ['KI13', 'KN13', 'KI18', 'KN18'],
           ['KS13', 'KX13', 'KS18', 'KX18'], ['LC13', 'LH13', 'LC18', 'LH18'],
           ['LM13', 'LR13', 'LM18', 'LR18'], ['LW13', 'MB13', 'LW18', 'MB18'],
           ['MG13', 'ML13', 'MG18', 'ML18'], ['MQ13', 'MV13', 'MQ18', 'MV18'],
           ['NA13', 'NF13', 'NA18', 'NF18'], ['NK13', 'NP13', 'NK18', 'NP18'],
           ['NU13', 'NZ13', 'NU18', 'NZ18'], ['OE13', 'OJ13', 'OE18', 'OJ18'],
           ['OO13', 'OT13', 'OO18', 'OT18'], ['OY13', 'PD13', 'OY18', 'PD18'],
           ['PI13', 'PN13', 'PI18', 'PN18'], ['PS13', 'PX13', 'PS18', 'PX18'],
           ['QC13', 'QH13', 'QC18', 'QH18'], ['QM13', 'QR13', 'QM18', 'QR18'],
           ['QW13', 'RB13', 'QW18', 'RB18'], ['RG13', 'RL13', 'RG18', 'RL18'],
           ['RQ13', 'RV13', 'RQ18', 'RV18'], ['SA13', 'SF13', 'SA18', 'SF18'],
           ['SK13', 'SP13', 'SK18', 'SP18'], ['SU13', 'SZ13', 'SU18', 'SZ18'],
           ['TE13', 'TJ13', 'TE18', 'TJ18'], ['TO13', 'TT13', 'TO18', 'TT18'],
           ['TY13', 'UD13', 'TY18', 'UD18'], ['UI13', 'UN13', 'UI18', 'UN18'],
           ['US13', 'UX13', 'US18', 'UX18'], ['VC13', 'VH13', 'VC18', 'VH18'],
           ['VM13', 'VR13', 'VM18', 'VR18'], ['VW13', 'WB13', 'VW18', 'WB18'],
           ['WG13', 'WL13', 'WG18', 'WL18'], ['WQ13', 'WV13', 'WQ18', 'WV18'],
           ['XA13', 'XF13', 'XA18', 'XF18'], ['XK13', 'XP13', 'XK18', 'XP18'],
           ['XU13', 'XZ13', 'XU18', 'XZ18'], ['YE13', 'YJ13', 'YE18', 'YJ18'],
           ['YO13', 'YT13', 'YO18', 'YT18'], ['YY13', 'ZD13', 'YY18', 'ZD18'],
           ['ZI13', 'ZN13', 'ZI18', 'ZN18'], ['ZS13', 'ZX13', 'ZS18', 'ZX18'],
           ['AAC13', 'AAH13', 'AAC18', 'AAH18'],
           ['AAM13', 'AAR13', 'AAM18', 'AAR18'],
           ['AAW13', 'ABB13', 'AAW18', 'ABB18']]

pro_2_6 = [['BM13', 'BR13'], ['BW13', 'CB13'],
           ['CG13', 'CL13'], ['CQ13', 'CV13'], ['DA13', 'DF13'],
           ['DK13', 'DP13'], ['DU13', 'DZ13'], ['EE13', 'EJ13'],
           ['EO13', 'ET13'], ['EY13', 'FD13'], ['FI13', 'FN13'],
           ['FS13', 'FX13'], ['GC13', 'GH13'], ['GM13', 'GR13'],
           ['GW13', 'HB13'], ['HG13', 'HL13'], ['HQ13', 'HV13'],
           ['IA13', 'IF13'], ['IK13', 'IP13'], ['IU13', 'IZ13'],
           ['JE13', 'JJ13'], ['JO13', 'JT13'], ['JY13', 'KD13'],
           ['KI13', 'KN13'], ['KS13', 'KX13'], ['LC13', 'LH13'],
           ['LM13', 'LR13'], ['LW13', 'MB13'], ['MG13', 'ML13'],
           ['MQ13', 'MV13'], ['NA13', 'NF13'], ['NK13', 'NP13'],
           ['NU13', 'NZ13'], ['OE13', 'OJ13'], ['OO13', 'OT13'],
           ['OY13', 'PD13'], ['PI13', 'PN13'], ['PS13', 'PX13'],
           ['QC13', 'QH13'], ['QM13', 'QR13'], ['QW13', 'RB13'],
           ['RG13', 'RL13'], ['RQ13', 'RV13'], ['SA13', 'SF13'],
           ['SK13', 'SP13'], ['SU13', 'SZ13'], ['TE13', 'TJ13'],
           ['TO13', 'TT13'], ['TY13', 'UD13'], ['UI13', 'UN13'],
           ['US13', 'UX13'], ['VC13', 'VH13'], ['VM13', 'VR13'],
           ['VW13', 'WB13'], ['WG13', 'WL13'], ['WQ13', 'WV13'],
           ['XA13', 'XF13'], ['XK13', 'XP13'], ['XU13', 'XZ13'],
           ['YE13', 'YJ13'], ['YO13', 'YT13'], ['YY13', 'ZD13'],
           ['ZI13', 'ZN13'], ['ZS13', 'ZX13'], ['AAC13', 'AAH13'],
           ['AAM13', 'AAR13'], ['AAW13', 'ABB13'], ['ABG13', 'ABL13'],
           ['ABQ13', 'ABV13'],
           ['ACA13', 'ACF13'],
           ['ACK13', 'ACP13'],
           ['ACU13', 'ACZ13'],
           ['ADE13', 'ADJ13'],
           ['ADO13', 'ADT13'],
           ['ADY13', 'AED13'],
           ['AEI13', 'AEN13'],
           ['AES13', 'AEX13'],
           ['AFC13', 'AFH13'],
           ['AFM13', 'AFR13'],
           ['AFW13', 'AGB13'],
           ['AGG13', 'AGL13'],
           ['AGQ13', 'AGV13'],
           ['AHA13', 'AHF13'],
           ['AHK13', 'AHP13'],
           ['AHU13', 'AHZ13'],
           ['AIE13', 'AIJ13'],
           ['AIO13', 'AIT13'],
           ['AIY13', 'AJD13'],
           ['AJI13', 'AJN13'],
           ['AJS13', 'AJX13'],
           ['AKC13', 'AKH13'],
           ['AKM13', 'AKR13'],
           ['AKW13', 'ALB13'],
           ['ALG13', 'ALL13'],
           ['ALQ13', 'ALV13'],
           ['AMA13', 'AMF13'],
           ['AMK13', 'AMP13'],
           ['AMU13', 'AMZ13'],
           ['ANE13', 'ANJ13'],
           ['ANO13', 'ANT13']]

pro_3_6 = [['BM13', 'BM18', 'BR18'], ['BW13', 'BW18', 'CB18'],
           ['CG13', 'CG18', 'CL18'], ['CQ13', 'CQ18', 'CV18'],
           ['DA13', 'DA18', 'DF18'], ['DK13', 'DK18', 'DP18'],
           ['DU13', 'DU18', 'DZ18'], ['EE13', 'EE18', 'EJ18'],
           ['EO13', 'EO18', 'ET18'], ['EY13', 'EY18', 'FD18'],
           ['FI13', 'FI18', 'FN18'], ['FS13', 'FS18', 'FX18'],
           ['GC13', 'GC18', 'GH18'], ['GM13', 'GM18', 'GR18'],
           ['GW13', 'GW18', 'HB18'], ['HG13', 'HG18', 'HL18'],
           ['HQ13', 'HQ18', 'HV18'], ['IA13', 'IA18', 'IF18'],
           ['IK13', 'IK18', 'IP18'], ['IU13', 'IU18', 'IZ18'],
           ['JE13', 'JE18', 'JJ18'], ['JO13', 'JO18', 'JT18'],
           ['JY13', 'KY18', 'KD18'], ['KI13', 'KI18', 'KN18'],
           ['KS13', 'KS18', 'KX18'], ['LC13', 'LC18', 'LH18'],
           ['LM13', 'LM18', 'LR18'], ['LW13', 'LW18', 'MB18'],
           ['MG13', 'MG18', 'ML18'], ['MQ13', 'MQ18', 'MV18'],
           ['NA13', 'NA18', 'NF18'], ['NK13', 'NK18', 'NP18'],
           ['NU13', 'NU18', 'NZ18'], ['OE13', 'OE18', 'OJ18'],
           ['OO13', 'OO18', 'OT18'], ['OY13', 'OY18', 'PD18'],
           ['PI13', 'PI18', 'PN18'], ['PS13', 'PS18', 'PX18'],
           ['QC13', 'QC18', 'QH18'], ['QM13', 'QM18', 'QR18'],
           ['QW13', 'QW18', 'RB18'], ['RG13', 'RG18', 'RL18'],
           ['RQ13', 'RQ18', 'RV18'], ['SA13', 'SA18', 'SF18'],
           ['SK13', 'SK18', 'SP18'], ['SU13', 'SU18', 'SZ18'],
           ['TE13', 'TE18', 'TJ18'], ['TO13', 'TO18', 'TT18'],
           ['TY13', 'TY18', 'UD18'], ['UI13', 'UI18', 'UN18'],
           ['US13', 'US18', 'UX18'], ['VC13', 'VC18', 'VH18'],
           ['VM13', 'VM18', 'VR18'], ['VW13', 'VW18', 'WB18'],
           ['WG13', 'WG18', 'WL18'], ['WQ13', 'WQ18', 'WV18'],
           ['XA13', 'XA18', 'XF18'], ['XK13', 'XK18', 'XP18'],
           ['XU13', 'XU18', 'XZ18'], ['YE13', 'YE18', 'YJ18'],
           ['YO13', 'YO18', 'YT18'], ['YY13', 'YY18', 'ZD18'],
           ['ZI13', 'ZI18', 'ZN18'], ['ZS13', 'ZS18', 'ZX18'],
           ['AAC13', 'AAC18', 'AAH18'], ['AAM13', 'AAM18', 'AAR18'],
           ['AAW13', 'AAW18', 'ABB18'], ['ABG13', 'ABG18', 'ABL18'],
           ['ABQ13', 'ABQ18', 'ABV18'],
           ['ACA13', 'ACA18', 'ACF18'],
           ['ACK13', 'ACK18', 'ACP18'],
           ['ACU13', 'ACU18', 'ACZ18'],
           ['ADE13', 'ADE18', 'ADJ18'],
           ['ADO13', 'ADO18', 'ADT18'],
           ['ADY13', 'ADY18', 'AED18'],
           ['AEI13', 'AEI18', 'AEN18'],
           ['AES13', 'AES18', 'AEX18'],
           ['AFC13', 'AFC18', 'AFH18'],
           ['AFM13', 'AFM18', 'AFR18'],
           ['AFW13', 'AFW18', 'AGB18'],
           ['AGG13', 'AGG18', 'AGL18'],
           ['AGQ13', 'AGQ18', 'AGV18'],
           ['AHA13', 'AHA18', 'AHF18'],
           ['AHK13', 'AHK18', 'AHP18'],
           ['AHU13', 'AHU18', 'AHZ18'],
           ['AIE13', 'AIE18', 'AIJ18'],
           ['AIO13', 'AIO18', 'AIT18'],
           ['AIY13', 'AIY18', 'AJD18'],
           ['AJI13', 'AJI18', 'AJN18'],
           ['AJS13', 'AJS18', 'AJX18'],
           ['AKC13', 'AKC18', 'AKH18'],
           ['AKM13', 'AKM18', 'AKR18'],
           ['AKW13', 'AKW18', 'ALB18'],
           ['ALG13', 'ALG18', 'ALL18'],
           ['ALQ13', 'ALQ18', 'ALV18'],
           ['AMA13', 'AMA18', 'AMF18'],
           ['AMK13', 'AMK18', 'AMP18'],
           ['AMU13', 'AMU18', 'AMZ18'],
           ['ANE13', 'ANE18', 'ANJ18'],
           ['ANO13', 'ANO18', 'ANT18']]

pro_4_6 = [['BM13', 'BR13', 'BM18', 'BR18'], ['BW13', 'CB13', 'BW18', 'CB18'],
           ['CG13', 'CL13', 'CG18', 'CL18'], ['CQ13', 'CV13', 'CQ18', 'CV18'],
           ['DA13', 'DF13', 'DA18', 'DF18'], ['DK13', 'DP13', 'DK18', 'DP18'],
           ['DU13', 'DZ13', 'DU18', 'DZ18'], ['EE13', 'EJ13', 'EE18', 'EJ18'],
           ['EO13', 'ET13', 'EO18', 'ET18'], ['EY13', 'FD13', 'EY18', 'FD18'],
           ['FI13', 'FN13', 'FI18', 'FN18'], ['FS13', 'FX13', 'FS18', 'FX18'],
           ['GC13', 'GH13', 'GC18', 'GH18'], ['GM13', 'GR13', 'GM18', 'GR18'],
           ['GW13', 'HB13', 'GW18', 'HB18'], ['HG13', 'HL13', 'HG18', 'HL18'],
           ['HQ13', 'HV13', 'HQ18', 'HV18'], ['IA13', 'IF13', 'IA18', 'IF18'],
           ['IK13', 'IP13', 'IK18', 'IP18'], ['IU13', 'IZ13', 'IU18', 'IZ18'],
           ['JE13', 'JJ13', 'JE18', 'JJ18'], ['JO13', 'JT13', 'JO18', 'JT18'],
           ['JY13', 'KD13', 'KY18', 'KD18'], ['KI13', 'KN13', 'KI18', 'KN18'],
           ['KS13', 'KX13', 'KS18', 'KX18'], ['LC13', 'LH13', 'LC18', 'LH18'],
           ['LM13', 'LR13', 'LM18', 'LR18'], ['LW13', 'MB13', 'LW18', 'MB18'],
           ['MG13', 'ML13', 'MG18', 'ML18'], ['MQ13', 'MV13', 'MQ18', 'MV18'],
           ['NA13', 'NF13', 'NA18', 'NF18'], ['NK13', 'NP13', 'NK18', 'NP18'],
           ['NU13', 'NZ13', 'NU18', 'NZ18'], ['OE13', 'OJ13', 'OE18', 'OJ18'],
           ['OO13', 'OT13', 'OO18', 'OT18'], ['OY13', 'PD13', 'OY18', 'PD18'],
           ['PI13', 'PN13', 'PI18', 'PN18'], ['PS13', 'PX13', 'PS18', 'PX18'],
           ['QC13', 'QH13', 'QC18', 'QH18'], ['QM13', 'QR13', 'QM18', 'QR18'],
           ['QW13', 'RB13', 'QW18', 'RB18'], ['RG13', 'RL13', 'RG18', 'RL18'],
           ['RQ13', 'RV13', 'RQ18', 'RV18'], ['SA13', 'SF13', 'SA18', 'SF18'],
           ['SK13', 'SP13', 'SK18', 'SP18'], ['SU13', 'SZ13', 'SU18', 'SZ18'],
           ['TE13', 'TJ13', 'TE18', 'TJ18'], ['TO13', 'TT13', 'TO18', 'TT18'],
           ['TY13', 'UD13', 'TY18', 'UD18'], ['UI13', 'UN13', 'UI18', 'UN18'],
           ['US13', 'UX13', 'US18', 'UX18'], ['VC13', 'VH13', 'VC18', 'VH18'],
           ['VM13', 'VR13', 'VM18', 'VR18'], ['VW13', 'WB13', 'VW18', 'WB18'],
           ['WG13', 'WL13', 'WG18', 'WL18'], ['WQ13', 'WV13', 'WQ18', 'WV18'],
           ['XA13', 'XF13', 'XA18', 'XF18'], ['XK13', 'XP13', 'XK18', 'XP18'],
           ['XU13', 'XZ13', 'XU18', 'XZ18'], ['YE13', 'YJ13', 'YE18', 'YJ18'],
           ['YO13', 'YT13', 'YO18', 'YT18'], ['YY13', 'ZD13', 'YY18', 'ZD18'],
           ['ZI13', 'ZN13', 'ZI18', 'ZN18'], ['ZS13', 'ZX13', 'ZS18', 'ZX18'],
           ['AAC13', 'AAH13', 'AAC18', 'AAH18'],
           ['AAM13', 'AAR13', 'AAM18', 'AAR18'],
           ['AAW13', 'ABB13', 'AAW18', 'ABB18'],
           ['ABG13', 'ABL13', 'ABG18', 'ABL18'],
           ['ABQ13', 'ABV13', 'ABQ18', 'ABV18'],
           ['ACA13', 'ACF13', 'ACA18', 'ACF18'],
           ['ACK13', 'ACP13', 'ACK18', 'ACP18'],
           ['ACU13', 'ACZ13', 'ACU18', 'ACZ18'],
           ['ADE13', 'ADJ13', 'ADE18', 'ADJ18'],
           ['ADO13', 'ADT13', 'ADO18', 'ADT18'],
           ['ADY13', 'AED13', 'ADY18', 'AED18'],
           ['AEI13', 'AEN13', 'AEI18', 'AEN18'],
           ['AES13', 'AEX13', 'AES18', 'AEX18'],
           ['AFC13', 'AFH13', 'AFC18', 'AFH18'],
           ['AFM13', 'AFR13', 'AFM18', 'AFR18'],
           ['AFW13', 'AGB13', 'AFW18', 'AGB18'],
           ['AGG13', 'AGL13', 'AGG18', 'AGL18'],
           ['AGQ13', 'AGV13', 'AGQ18', 'AGV18'],
           ['AHA13', 'AHF13', 'AHA18', 'AHF18'],
           ['AHK13', 'AHP13', 'AHK18', 'AHP18'],
           ['AHU13', 'AHZ13', 'AHU18', 'AHZ18'],
           ['AIE13', 'AIJ13', 'AIE18', 'AIJ18'],
           ['AIO13', 'AIT13', 'AIO18', 'AIT18'],
           ['AIY13', 'AJD13', 'AIY18', 'AJD18'],
           ['AJI13', 'AJN13', 'AJI18', 'AJN18'],
           ['AJS13', 'AJX13', 'AJS18', 'AJX18'],
           ['AKC13', 'AKH13', 'AKC18', 'AKH18'],
           ['AKM13', 'AKR13', 'AKM18', 'AKR18'],
           ['AKW13', 'ALB13', 'AKW18', 'ALB18'],
           ['ALG13', 'ALL13', 'ALG18', 'ALL18'],
           ['ALQ13', 'ALV13', 'ALQ18', 'ALV18'],
           ['AMA13', 'AMF13', 'AMA18', 'AMF18'],
           ['AMK13', 'AMP13', 'AMK18', 'AMP18'],
           ['AMU13', 'AMZ13', 'AMU18', 'AMZ18'],
           ['ANE13', 'ANJ13', 'ANE18', 'ANJ18'],
           ['ANO13', 'ANT13', 'ANO18', 'ANT18']]

skm_cell = ['A7', 'K7', 'U7', 'AE7', 'AO7', 'AY7']

# File Structor Operation 위치
root = r"C:\Users\vivans\Desktop\올포홈\test\〔2〕   사 진 대 장"
#####################################################################################################
# File Structor Operation 결과값 불러오기
df = pd.read_csv(r"C:\Users\vivans\Desktop\올포홈\out_filepath2.csv", encoding='cp949')
start = time.time()
for i in range(len(df)):  # df = File sub-folders Result
    if df.iloc[i].depth == 1:
        root2 = root + "\\" + df.iloc[i].subfolder
        list = os.listdir(root2)
        xlsx = [li for li in list if li.endswith(".xlsx")]
        df2 = pd.read_excel(root2 + "\\" + xlsx[0])  # df2 = Complete List (완료처리 리스트)
        for j in range(len(df2)):
            arr = [4, 8, 12, 16, 20, 24, 28, 32, 36, 44, 48, 60, 64, 72, 80, 92,
                   120, 160, 400]
            result_form = []
            path_last = []
            num_files = 0
            num_form = 0
            copy_root = ""
            copy_name = ""
            count = 0
            count_two = 0
            rotate_path = []
            list_path = []
            jpg_list = []
            first_check = True
            pic2_check = False
            temp_bool = False
            folder_bool = False
            job_bool = False
            memories = []
            # 1 사진 대장 폼 선택
            # 1.1 파일 개수 체크 ( Last_path * 4
            for i in range(len(df)):
                if df2['접수일련번호'][j] in df.iloc[i].subfolder:
                    if df.iloc[i].depth > 3:
                        if df.iloc[i].num_subfolders == 0:
                            jpg_list.append(i)
            for i in range(len(jpg_list)):
                list = os.listdir(root + "\\" + df.iloc[jpg_list[i]].subfolder)
                jpg_list1 = [li for li in list if li.endswith((".jpg", ".JPG"))]
                list2 = os.listdir(root + "\\" + df.iloc[jpg_list[i - 1]].subfolder)
                jpg_list2 = [li for li in list2 if li.endswith((".jpg", ".JPG"))]
                if len(jpg_list1) != 2:
                    num_files += 1
                    first_check = False
                    pic2_check = False
                    memories.append(0)
                else:
                    if first_check == True:
                        num_files += 1
                        first_check = False
                        pic2_check = True
                        memories.append(0)
                    elif pic2_check == True:
                        pic2_check = False
                        memories.append(1)
                    else:
                        pic2_check = True
                        num_files += 1
                        memories.append(0)
            num_files = num_files * 4
            # 1.2 개수에 맞는 폼 선택
            for i in range(len(arr)):
                if num_files <= arr[i]:  # 파일 개수 보다 같거나 큰 폼을 선택
                    num_form = arr[i]
                    break
            # 1.3 하자처리확인서 개수 확인
            for i in range(len(df)):
                if df2['접수일련번호'][j] in df.iloc[i].subfolder:
                    if df.iloc[i].depth == 3:
                        list = os.listdir(root + "\\" + df.iloc[i].subfolder)
                        list_jpg = [li for li in list if li.endswith((".jpg", ".JPG"))]
                        form_type = 0
                        for i in range(len(list_jpg)):
                            if "SKM" in list_jpg[i]:  # 하자처리 개수에 맞춰 파일명 지정
                                form_type += 1
                        num_form = str(num_form) + "-" + str(
                            form_type) + ".xlsx"
                        print("사진대장 양식 : " + num_form)
            # 2 사진 대장 양식 복사
            # copy_root = 루트폴더 바로 밑 폴더
            # copy_name = 완료 폴더와 동일한 폴더명
            for i in range(len(df)):
                if df2['접수일련번호'][j] in df.iloc[i].subfolder:
                    if df.iloc[i].depth == 3:
                        copy_root = root + "\\" + df.iloc[i].subfolder + "\\"
                        break
            copy_name = os.path.basename(os.path.normpath(df.iloc[i].subfolder))
            try:
                shutil.copy(
                    r"X:\〔99〕   rpa_setting\사진대장 양식" + "\\" + num_form,
                    copy_root + copy_name + ".xlsx")
                print(copy_name + " 사진양식 복사 완료")
            except Exception as e:
                print("사진양식 복사 실패", e)
            # 3 사진대장 작업명칭 뽑아내기
            # 접수일련번호와 동일한 폴더를 가진 depth 3이상,
            # num_subfolder 0의 폴더명을 result_form 에 Append
            for i in range(len(df)):
                if df2['접수일련번호'][j] in df.iloc[i].subfolder:
                    if df.iloc[i].depth > 3:
                        if df.iloc[i].num_subfolders == 0:
                            re_temp = re.sub('^\d{2}\s', '', os.path.basename(
                                os.path.normpath(df.iloc[i].subfolder)))
                            result_form.append(re.sub('-\d', '', re_temp))
                            path_last.append(df.iloc[i].subfolder)
            #############################################################
            # 4.1 작업완료 리스트에서 행 뽑아 사진대장 A2 행에 붙여넣기
            # list_var = 완료리스트 (ex:A2:AN2)
            wb2 = openpyxl.load_workbook(root2 + "\\" + xlsx[0])
            ws2 = wb2['Sheet1']
            cells = ws2['a' + str(j + 2):'AN' + str(j + 2)]
            list_var = []
            for row in cells:
                for cell in row:
                    list_var.append(cell.value)
            # 4.2 사진 대장에 작업 명칭 삽입 및 저장
            wb = openpyxl.load_workbook(copy_root + copy_name + ".xlsx")
            ws = wb['사진대지']
            if list_var[39] is not None:
                if type(list_var[39]) != str:
                    list_var[39] = list_var[39].strftime('%Y-%m-%d')
            for p in range(len(list_var)):
                ws[comp_list[p]] = list_var[p]  # A2 : AN2 입력
            try:
                if list_var[38].find('다가구') > 0:
                    ws['D4'] = list_var[5][5:7]
            except AttributeError:
                pass
            if "-1" in num_form:
                for i in range(len(result_form)):
                    if memories[i] == 0:
                        ws[job_name_top[count_two]] = result_form[i]
                        ws[job_name_bottom[count_two]] = result_form[i]
                        count_two += 1
                    elif memories[i] == 1:
                        ws[job_name_bottom[count_two - 1]] = result_form[i]
                for i in range(len(df)):
                    if df2['접수일련번호'][j] in df.iloc[i].subfolder:
                        if df.iloc[i].depth == 3:
                            for c in range(len(list_jpg)):
                                if "SKM" in list_jpg[c]:
                                    im = Image.open(root + "\\" + df.iloc[
                                        i].subfolder + "\\" + list_jpg[c])
                                    im = im.transpose(
                                        Image.ROTATE_90)  # 하자처리 확인서 회전
                                    im.save(root + "\\" + df.iloc[
                                        i].subfolder + "\\roate_" + list_jpg[
                                                c])  # 회전 후 확인서 저장
                                    img = openpyxl.drawing.image.Image(
                                        root + "\\" + df.iloc[
                                            i].subfolder + "\\roate_" +
                                        list_jpg[c])
                                    img.width = 935
                                    img.height = 687
                                    ws.add_image(img, 'A7')
                                    rotate_path.append(root + "\\" + df.iloc[
                                        i].subfolder + "\\roate_" + list_jpg[
                                                           c])  # 수정본 삭제하기 위해 삽입된 이미지 path 저장
                for i in range(len(jpg_list)):
                    list = os.listdir(
                        root + "\\" + df.iloc[jpg_list[i]].subfolder)
                    jpg_list1 = [li for li in list if
                                 li.endswith(".jpg")]
                    if (4 <= len(list)):
                        # 이미지가 4 개 이상 일 경우
                        for p in range(4):
                            image = openpyxl.drawing.image.Image(
                                root + "\\" + df.iloc[
                                    jpg_list[i]].subfolder + "\\" + list[p])
                            image.width = 363
                            image.height = 273
                            # check_name(p, "4")
                            ws.add_image(image, pic_4[count][p])
                        count += 1
                    elif (len(list)) == 3:
                        for p in range(3):
                            image = openpyxl.drawing.image.Image(
                                root + "\\" + df.iloc[
                                    jpg_list[i]].subfolder + "\\" + list[p])
                            image.width = 363
                            image.height = 273
                            # check_name(p, "3")
                            ws.add_image(image, pic_3[count][p])
                        count += 1
                    elif (len(list)) == 2 and memories[i] == 1:
                        for p in range(2):
                            image = openpyxl.drawing.image.Image(
                                root + "\\" + df.iloc[
                                    jpg_list[i]].subfolder + "\\" + list[p])
                            image.width = 363
                            image.height = 273
                            # check_name(p, "2")
                            ws.add_image(image,
                                         pic_2_merged[count - 1][p])
                    elif (len(list)) == 2 and memories[i] == 0:
                        for p in range(2):
                            image = openpyxl.drawing.image.Image(
                                root + "\\" + df.iloc[
                                    jpg_list[i]].subfolder + "\\" + list[p])
                            image.width = 363
                            image.height = 273
                            # check_name(p, "2")
                            ws.add_image(image, pic_2[count][p])
                        count += 1
                    elif (len(list)) == 1:
                        image1 = openpyxl.drawing.image.Image(
                            root + "\\" + df.iloc[
                                jpg_list[i]].subfolder + "\\" + list[0])
                        image1.width = 363
                        image1.height = 273
                        ws.add_image(image1, pic_1[count][0])
                        image2 = openpyxl.drawing.image.Image(
                            root + "\\" + df.iloc[
                                jpg_list[i]].subfolder + "\\" + list[0])
                        image2.width = 363
                        image2.height = 273
                        ws.add_image(image2, pic_1[count][1])
                        count += 1
                    elif (len(list)) == 0:
                        count += 1
            elif "-2" in num_form:
                for i in range(len(result_form)):
                    if memories[i] == 0:
                        ws[job_name_top_2[count_two]] = result_form[i]
                        ws[job_name_bottom_2[count_two]] = result_form[i]
                        count_two += 1
                    elif memories[i] == 1:
                        ws[job_name_bottom_2[count_two - 1]] = result_form[i]
                for i in range(len(df)):
                    if df2['접수일련번호'][j] in df.iloc[i].subfolder:
                        if df.iloc[i].depth == 3:
                            for c in range(len(list_jpg)):
                                if "SKM" in list_jpg[c]:
                                    im = Image.open(root + "\\" + df.iloc[
                                        i].subfolder + "\\" + list_jpg[c])
                                    im = im.transpose(Image.ROTATE_90)
                                    im.save(root + "\\" + df.iloc[
                                        i].subfolder + "\\roate_" + list_jpg[c])
                                    img = openpyxl.drawing.image.Image(
                                        root + "\\" + df.iloc[
                                            i].subfolder + "\\roate_" +
                                        list_jpg[c])
                                    img.width = 935
                                    img.height = 687
                                    ws.add_image(img, skm_cell[c])
                                    rotate_path.append(root + "\\" + df.iloc[
                                        i].subfolder + "\\roate_" + list_jpg[c])
                for i in range(len(jpg_list)):
                    list = os.listdir(
                        root + "\\" + df.iloc[jpg_list[i]].subfolder)
                    jpg_list1 = [li for li in list if
                                 li.endswith(".jpg")]
                    if (4 <= len(list)):
                        # 이미지가 4 개 이상 일 경우
                        for p in range(4):
                            image = openpyxl.drawing.image.Image(
                                root + "\\" + df.iloc[
                                    jpg_list[i]].subfolder + "\\" + list[p])
                            image.width = 363
                            image.height = 273
                            # check_name(p,"4_2")
                            ws.add_image(image, pic_4_2[count][p])
                        count += 1
                    elif (len(list)) == 3:
                        # 이미지가 3 개 이상 일 경우
                        for p in range(3):
                            image = openpyxl.drawing.image.Image(
                                root + "\\" + df.iloc[
                                    jpg_list[i]].subfolder + "\\" + list[p])
                            image.width = 363
                            image.height = 273
                            # check_name(p, "3_2")
                            ws.add_image(image, pic_3_2[count][p])
                        count += 1
                    elif (len(list)) == 2 and memories[i] == 1:
                        for p in range(2):
                            image = openpyxl.drawing.image.Image(
                                root + "\\" + df.iloc[
                                    jpg_list[i]].subfolder + "\\" + list[p])
                            image.width = 363
                            image.height = 273
                            # check_name(p, "2")
                            ws.add_image(image,
                                         pic_2_2_merged[count - 1][
                                             p])
                    elif (len(list)) == 2 and memories[i] == 0:
                        for p in range(2):
                            image = openpyxl.drawing.image.Image(
                                root + "\\" + df.iloc[
                                    jpg_list[i]].subfolder + "\\" + list[p])
                            image.width = 363
                            image.height = 273
                            # check_name(p, "2_2")
                            ws.add_image(image, pic_2_2[count][p])
                        count += 1
                    elif (len(list)) == 1:
                        image1 = openpyxl.drawing.image.Image(
                            root + "\\" + df.iloc[
                                jpg_list[i]].subfolder + "\\" + list[0])
                        image1.width = 363
                        image1.height = 273
                        ws.add_image(image1, pic_1_2[count][0])
                        image2 = openpyxl.drawing.image.Image(
                            root + "\\" + df.iloc[
                                jpg_list[i]].subfolder + "\\" + list[0])
                        image2.width = 363
                        image2.height = 273
                        ws.add_image(image2, pic_1_2[count][1])
                        count += 1
                    elif (len(list)) == 0:
                        count += 1
            elif "-3" in num_form:
                for i in range(len(result_form)):
                    if memories[i] == 0:
                        ws[job_name_top_3[count_two]] = result_form[i]
                        ws[job_name_bottom_3[count_two]] = result_form[
                            i]
                        count_two += 1
                    elif memories[i] == 1:
                        ws[job_name_bottom_3[count_two - 1]] = \
                            result_form[i]
                for i in range(len(df)):
                    if df2['접수일련번호'][j] in df.iloc[i].subfolder:
                        if df.iloc[i].depth == 3:
                            for c in range(len(list_jpg)):
                                if "SKM" in list_jpg[c]:
                                    im = Image.open(
                                        root + "\\" + df.iloc[
                                            i].subfolder + "\\" +
                                        list_jpg[c])
                                    im = im.transpose(Image.ROTATE_90)
                                    im.save(root + "\\" + df.iloc[
                                        i].subfolder + "\\roate_" +
                                            list_jpg[c])
                                    img = openpyxl.drawing.image.Image(
                                        root + "\\" + df.iloc[
                                            i].subfolder + "\\roate_" +
                                        list_jpg[c])
                                    img.width = 935
                                    img.height = 687
                                    ws.add_image(img, skm_cell[c])
                                    rotate_path.append(
                                        root + "\\" + df.iloc[
                                            i].subfolder + "\\roate_" +
                                        list_jpg[c])
                for i in range(len(jpg_list)):
                    list = os.listdir(
                        root + "\\" + df.iloc[jpg_list[i]].subfolder)
                    jpg_list1 = [li for li in list if
                                 li.endswith(".jpg")]
                    if (4 <= len(list)):
                        # 이미지가 4 개 이상 일 경우
                        for p in range(4):
                            image = openpyxl.drawing.image.Image(
                                root + "\\" + df.iloc[
                                    jpg_list[i]].subfolder + "\\" +
                                list[p])
                            image.width = 363
                            image.height = 273
                            # check_name(p,"4_2")
                            ws.add_image(image, pic_4_3[count][p])
                        count += 1
                    elif (len(list)) == 3:
                        # 이미지가 3 개 이상 일 경우
                        for p in range(3):
                            image = openpyxl.drawing.image.Image(
                                root + "\\" + df.iloc[
                                    jpg_list[i]].subfolder + "\\" +
                                list[p])
                            image.width = 363
                            image.height = 273
                            # check_name(p, "3_2")
                            ws.add_image(image, pic_3_3[count][p])
                        count += 1
                    elif (len(list)) == 2 and memories[i] == 1:
                        for p in range(2):
                            image = openpyxl.drawing.image.Image(
                                root + "\\" + df.iloc[
                                    jpg_list[i]].subfolder + "\\" +
                                list[p])
                            image.width = 363
                            image.height = 273
                            # check_name(p, "2")
                            ws.add_image(image,
                                         pic_2_3_merged[count - 1][
                                             p])
                    elif (len(list)) == 2 and memories[i] == 0:
                        for p in range(2):
                            image = openpyxl.drawing.image.Image(
                                root + "\\" + df.iloc[
                                    jpg_list[i]].subfolder + "\\" +
                                list[p])
                            image.width = 363
                            image.height = 273
                            # check_name(p, "2_2")
                            ws.add_image(image, pic_2_3[count][p])
                        count += 1
                    elif (len(list)) == 1:
                        image1 = openpyxl.drawing.image.Image(
                            root + "\\" + df.iloc[
                                jpg_list[i]].subfolder + "\\" + list[0])
                        image1.width = 363
                        image1.height = 273
                        ws.add_image(image1, pic_1_3[count][0])
                        image2 = openpyxl.drawing.image.Image(
                            root + "\\" + df.iloc[
                                jpg_list[i]].subfolder + "\\" + list[0])
                        image2.width = 363
                        image2.height = 273
                        ws.add_image(image2, pic_1_3[count][1])
                        count += 1
                    elif (len(list)) == 0:
                        count += 1
            elif "-4" in num_form:
                for i in range(len(result_form)):
                    if memories[i] == 0:
                        ws[job_name_top_4[count_two]] = result_form[i]
                        ws[job_name_bottom_4[count_two]] = result_form[
                            i]
                        count_two += 1
                    elif memories[i] == 1:
                        ws[job_name_bottom_4[count_two - 1]] = \
                            result_form[i]
                for i in range(len(df)):
                    if df2['접수일련번호'][j] in df.iloc[i].subfolder:
                        if df.iloc[i].depth == 3:
                            for c in range(len(list_jpg)):
                                if "SKM" in list_jpg[c]:
                                    im = Image.open(
                                        root + "\\" + df.iloc[
                                            i].subfolder + "\\" +
                                        list_jpg[c])
                                    im = im.transpose(Image.ROTATE_90)
                                    im.save(root + "\\" + df.iloc[
                                        i].subfolder + "\\roate_" +
                                            list_jpg[c])
                                    img = openpyxl.drawing.image.Image(
                                        root + "\\" + df.iloc[
                                            i].subfolder + "\\roate_" +
                                        list_jpg[c])
                                    img.width = 935
                                    img.height = 687
                                    ws.add_image(img, skm_cell[c])
                                    rotate_path.append(
                                        root + "\\" + df.iloc[
                                            i].subfolder + "\\roate_" +
                                        list_jpg[c])
                for i in range(len(jpg_list)):
                    list = os.listdir(
                        root + "\\" + df.iloc[jpg_list[i]].subfolder)
                    jpg_list1 = [li for li in list if
                                 li.endswith(".jpg")]
                    if (4 <= len(list)):
                        # 이미지가 4 개 이상 일 경우
                        for p in range(4):
                            image = openpyxl.drawing.image.Image(
                                root + "\\" + df.iloc[
                                    jpg_list[i]].subfolder + "\\" +
                                list[p])
                            image.width = 363
                            image.height = 273
                            # check_name(p,"4_2")
                            ws.add_image(image, pic_4_4[count][p])
                        count += 1
                    elif (len(list)) == 3:
                        # 이미지가 3 개 이상 일 경우
                        for p in range(3):
                            image = openpyxl.drawing.image.Image(
                                root + "\\" + df.iloc[
                                    jpg_list[i]].subfolder + "\\" +
                                list[p])
                            image.width = 363
                            image.height = 273
                            # check_name(p, "3_2")
                            ws.add_image(image, pic_3_4[count][p])
                        count += 1
                    elif (len(list)) == 2 and memories[i] == 1:
                        for p in range(2):
                            image = openpyxl.drawing.image.Image(
                                root + "\\" + df.iloc[
                                    jpg_list[i]].subfolder + "\\" +
                                list[p])
                            image.width = 363
                            image.height = 273
                            # check_name(p, "2")
                            ws.add_image(image,
                                         pic_2_4_merged[count - 1][
                                             p])
                    elif (len(list)) == 2 and memories[i] == 0:
                        for p in range(2):
                            image = openpyxl.drawing.image.Image(
                                root + "\\" + df.iloc[
                                    jpg_list[i]].subfolder + "\\" +
                                list[p])
                            image.width = 363
                            image.height = 273
                            # check_name(p, "2_2")
                            ws.add_image(image, pic_2_4[count][p])
                        count += 1
                    elif (len(list)) == 1:
                        image1 = openpyxl.drawing.image.Image(
                            root + "\\" + df.iloc[
                                jpg_list[i]].subfolder + "\\" + list[0])
                        image1.width = 363
                        image1.height = 273
                        ws.add_image(image1, pic_1_4[count][0])
                        image2 = openpyxl.drawing.image.Image(
                            root + "\\" + df.iloc[
                                jpg_list[i]].subfolder + "\\" + list[0])
                        image2.width = 363
                        image2.height = 273
                        ws.add_image(image2, pic_1_4[count][1])
                        count += 1
                    elif (len(list)) == 0:
                        count += 1
            elif "-5" in num_form:
                for i in range(len(result_form)):
                    if memories[i] == 0:
                        ws[job_name_top_5[count_two]] = result_form[i]
                        ws[job_name_bottom_5[count_two]] = result_form[
                            i]
                        count_two += 1
                    elif memories[i] == 1:
                        ws[job_name_bottom_5[count_two - 1]] = \
                        result_form[i]
                for i in range(len(df)):
                    if df2['접수일련번호'][j] in df.iloc[i].subfolder:
                        if df.iloc[i].depth == 3:
                            for c in range(len(list_jpg)):
                                if "SKM" in list_jpg[c]:
                                    im = Image.open(
                                        root + "\\" + df.iloc[
                                            i].subfolder + "\\" +
                                        list_jpg[c])
                                    im = im.transpose(Image.ROTATE_90)
                                    im.save(root + "\\" + df.iloc[
                                        i].subfolder + "\\roate_" +
                                            list_jpg[c])
                                    img = openpyxl.drawing.image.Image(
                                        root + "\\" + df.iloc[
                                            i].subfolder + "\\roate_" +
                                        list_jpg[c])
                                    img.width = 935
                                    img.height = 687
                                    ws.add_image(img, skm_cell[c])
                                    rotate_path.append(
                                        root + "\\" + df.iloc[
                                            i].subfolder + "\\roate_" +
                                        list_jpg[c])
                for i in range(len(jpg_list)):
                    list = os.listdir(
                        root + "\\" + df.iloc[jpg_list[i]].subfolder)
                    jpg_list1 = [li for li in list if
                                 li.endswith(".jpg")]
                    if (4 <= len(list)):
                        # 이미지가 4 개 이상 일 경우
                        for p in range(4):
                            image = openpyxl.drawing.image.Image(
                                root + "\\" + df.iloc[
                                    jpg_list[i]].subfolder + "\\" +
                                list[p])
                            image.width = 363
                            image.height = 273
                            # check_name(p,"4_2")
                            ws.add_image(image, pic_4_5[count][p])
                        count += 1
                    elif (len(list)) == 3:
                        # 이미지가 3 개 이상 일 경우
                        for p in range(3):
                            image = openpyxl.drawing.image.Image(
                                root + "\\" + df.iloc[
                                    jpg_list[i]].subfolder + "\\" +
                                list[p])
                            image.width = 363
                            image.height = 273
                            # check_name(p, "3_2")
                            ws.add_image(image, pic_3_5[count][p])
                        count += 1
                    elif (len(list)) == 2 and memories[i] == 1:
                        for p in range(2):
                            image = openpyxl.drawing.image.Image(
                                root + "\\" + df.iloc[
                                    jpg_list[i]].subfolder + "\\" +
                                list[p])
                            image.width = 363
                            image.height = 273
                            # check_name(p, "2")
                            ws.add_image(image,
                                         pic_2_5_merged[count - 1][
                                             p])
                    elif (len(list)) == 2 and memories[i] == 0:
                        for p in range(2):
                            image = openpyxl.drawing.image.Image(
                                root + "\\" + df.iloc[
                                    jpg_list[i]].subfolder + "\\" +
                                list[p])
                            image.width = 363
                            image.height = 273
                            # check_name(p, "2_2")
                            ws.add_image(image, pic_2_5[count][p])
                        count += 1
                    elif (len(list)) == 1:
                        image1 = openpyxl.drawing.image.Image(
                            root + "\\" + df.iloc[
                                jpg_list[i]].subfolder + "\\" + list[0])
                        image1.width = 363
                        image1.height = 273
                        ws.add_image(image1, pic_1_5[count][0])
                        image2 = openpyxl.drawing.image.Image(
                            root + "\\" + df.iloc[
                                jpg_list[i]].subfolder + "\\" + list[0])
                        image2.width = 363
                        image2.height = 273
                        ws.add_image(image2, pic_1_5[count][1])
                        count += 1
                    elif (len(list)) == 0:
                        count += 1
            elif "-6" in num_form:
                for i in range(len(result_form)):
                    if memories[i] == 0:
                        ws[job_name_top_6[count_two]] = result_form[i]
                        ws[job_name_bottom_6[count_two]] = result_form[
                            i]
                        count_two += 1
                    elif memories[i] == 1:
                        ws[job_name_bottom_6[count_two - 1]] = \
                        result_form[i]
                for i in range(len(df)):
                    if df2['접수일련번호'][j] in df.iloc[i].subfolder:
                        if df.iloc[i].depth == 3:
                            for c in range(len(list_jpg)):
                                if "SKM" in list_jpg[c]:
                                    im = Image.open(
                                        root + "\\" + df.iloc[
                                            i].subfolder + "\\" +
                                        list_jpg[c])
                                    im = im.transpose(Image.ROTATE_90)
                                    im.save(root + "\\" + df.iloc[
                                        i].subfolder + "\\roate_" +
                                            list_jpg[c])
                                    img = openpyxl.drawing.image.Image(
                                        root + "\\" + df.iloc[
                                            i].subfolder + "\\roate_" +
                                        list_jpg[c])
                                    img.width = 935
                                    img.height = 687
                                    ws.add_image(img, skm_cell[c])
                                    rotate_path.append(
                                        root + "\\" + df.iloc[
                                            i].subfolder + "\\roate_" +
                                        list_jpg[c])
                for i in range(len(jpg_list)):
                    list = os.listdir(
                        root + "\\" + df.iloc[jpg_list[i]].subfolder)
                    jpg_list1 = [li for li in list if
                                 li.endswith(".jpg")]
                    if (4 <= len(list)):
                        # 이미지가 4 개 이상 일 경우
                        for p in range(4):
                            image = openpyxl.drawing.image.Image(
                                root + "\\" + df.iloc[
                                    jpg_list[i]].subfolder + "\\" +
                                list[p])
                            image.width = 363
                            image.height = 273
                            # check_name(p,"4_2")
                            ws.add_image(image, pic_4_6[count][p])
                        count += 1
                    elif (len(list)) == 3:
                        # 이미지가 3 개 이상 일 경우
                        for p in range(3):
                            image = openpyxl.drawing.image.Image(
                                root + "\\" + df.iloc[
                                    jpg_list[i]].subfolder + "\\" +
                                list[p])
                            image.width = 363
                            image.height = 273
                            # check_name(p, "3_2")
                            ws.add_image(image, pic_3_6[count][p])
                        count += 1
                    elif (len(list)) == 2 and memories[i] == 1:
                        for p in range(2):
                            image = openpyxl.drawing.image.Image(
                                root + "\\" + df.iloc[
                                    jpg_list[i]].subfolder + "\\" +
                                list[p])
                            image.width = 363
                            image.height = 273
                            # check_name(p, "2")
                            ws.add_image(image,
                                         pic_2_6_merged[count - 1][
                                             p])
                    elif (len(list)) == 2 and memories[i] == 0:
                        for p in range(2):
                            image = openpyxl.drawing.image.Image(
                                root + "\\" + df.iloc[
                                    jpg_list[i]].subfolder + "\\" +
                                list[p])
                            image.width = 363
                            image.height = 273
                            # check_name(p, "2_2")
                            ws.add_image(image, pic_2_6[count][p])
                        count += 1
                    elif (len(list)) == 1:
                        image1 = openpyxl.drawing.image.Image(
                            root + "\\" + df.iloc[
                                jpg_list[i]].subfolder + "\\" + list[0])
                        image1.width = 363
                        image1.height = 273
                        ws.add_image(image1, pic_1_6[count][0])
                        image2 = openpyxl.drawing.image.Image(
                            root + "\\" + df.iloc[
                                jpg_list[i]].subfolder + "\\" + list[0])
                        image2.width = 363
                        image2.height = 273
                        ws.add_image(image2, pic_1_6[count][1])
                        count += 1
                    elif (len(list)) == 0:
                        count += 1
            print("작업 사진 삽입 완료")
            try:
                wb.save(copy_root + copy_name + ".xlsx")
                count = 0;
                print("작업 완료\n")
                for i in rotate_path:
                    os.remove(i)
            except:
                print("작업 실패\n\n")

print("사진대장 완료 폴더 이동\n\n")
lists = os.listdir(r"X:\〔2〕   사 진 대 장")
for i in lists:
    shutil.move(r"X:\〔2〕   사 진 대 장" + "\\" + i, r"X:\〔2〕   사 진 대 장 = 완료" + "\\" + i)
print(" Time :", round(time.time() - start,2),"s")
time.sleep(5000)
