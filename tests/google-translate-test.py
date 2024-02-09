from kwiq.core.app import App
from kwiq.core.flow import Flow
from kwiq.task.google_translate import GoogleTranslate


class TestFlow(Flow):

    def fn(self, text: str) -> str:
        print("In TestFlow... text: ", text)
        return GoogleTranslate().execute(text=text)


def main():
    app = App(name='TestApp')

    # register a new flow...
    app.register_flow(TestFlow(name="TestFlow"))

    app.run('TestFlow', text="再见")


if __name__ == '__main__':
    main()
