import importlib.util
import tempfile
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('native_send',Path(__file__).parents[1]/'scripts/hermes_native_send.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)

class NativeSendEnvironmentTests(unittest.TestCase):
    def test_existing_file_loaded_into_child_environment_only(self):
        with tempfile.TemporaryDirectory() as d:
            token=Path(d)/'token';token.write_text('fixture-token\n')
            original={'PATH':'/bin','TELEGRAM_BOT_TOKEN':'wrong'}
            result=p.send_environment({'telegram_bot_token_file':str(token),'telegram_home_channel':'fixture-owner'},original)
            self.assertEqual(result['TELEGRAM_BOT_TOKEN'],'fixture-token')
            self.assertEqual(result['TELEGRAM_HOME_CHANNEL'],'fixture-owner')
            self.assertEqual(original['TELEGRAM_BOT_TOKEN'],'wrong')
            self.assertEqual(token.read_text(),'fixture-token\n')
            self.assertEqual(list(Path(d).iterdir()),[token])

    def test_missing_credentials_fail_without_sending(self):
        with self.assertRaises(ValueError):p.send_environment({'telegram_bot_token_file':'relative','telegram_home_channel':'home'}, {})
        with tempfile.TemporaryDirectory() as d:
            token=Path(d)/'token';token.write_text('')
            with self.assertRaises(ValueError):p.send_environment({'telegram_bot_token_file':str(token),'telegram_home_channel':'home'}, {})

if __name__=='__main__':unittest.main()
