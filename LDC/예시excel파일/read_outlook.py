from exchangelib import Credentials, Account, HTMLBody

def read_outlook_mailbox(account, mailbox_name):
    # 특정 메일함 선택
    mailbox = account.root / 'Top of Information Store' / mailbox_name

    # 메일함 내 메일을 날짜 기준으로 내림차순으로 정렬하여 읽기
    for item in mailbox.all().order_by('-datetime_received'):
        print("제목:", item.subject)
        print("보낸이:", item.sender.email_address)
        print("날짜:", item.datetime_received)
        print("내용:", HTMLBody(item.body))
        print("-" * 50)

if __name__ == "__main__":
    # 이미 로그인된 Outlook 계정 객체 생성
    account = Account()

    # 읽어올 메일함의 이름 설정
    target_mailbox_name = "jira"

    # Outlook 메일함 읽기 함수 호출
    read_outlook_mailbox(account, target_mailbox_name)
