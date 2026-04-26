from environs import Env
from gigachat import GigaChat

env = Env()
env.read_env()


giga = GigaChat(
    credentials=env.str("GIGACHAT_CREDENTIALS"),
    scope=env.str("GIGACHAT_SCOPE", "GIGACHAT_API_PERS"),
    model=env.str("GIGACHAT_MODEL", "GigaChat"),
    verify_ssl_certs=False
)


def ask_giga(prompt: str) -> str:
   response = giga.chat(prompt)
   return response.choices[0].message.content


def main():
   print("Введите сообщение (exit для выхода)")

   while True:
      user_input = input("Промт: ")

      if user_input.lower() == "exit":
         break

      answer = ask_giga(user_input)
      print("Ответ ИИ:", answer)


if __name__ == "__main__":
   main()