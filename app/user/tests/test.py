const = {'email': 'abc@com', 'user': 'test', 'change': 'None'}

class test:
    def testing(self):
        test = const.copy()
        print('test = ', test, 'const = ', const)
        test['change'] = 'Yes'
        print('after change')
        print('test = ', test, 'const = ', const)

if __name__ == '__main__':
    test().testing()