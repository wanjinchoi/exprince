import win32com.client as win32


hwp = win32.gencache.EnsureDispatch("HWPFrame.HwpObject")
##https://www.hancom.com/board/devdataView.do?board_seq=47&artcl_seq=4085&pageInfo.page=&search_text=HKEY_CURRENT_USER\SOFTWARE\HNC\HwpAutomation\Modules

hwp.RegisterModule("FilePathCheckDLL", "FilePathCheckerModule")


hwp.Open("C:\\work\\nong\\출장결과보고서_오창사용전검사.hwp")





print('\n', hwp.GetFieldList())
