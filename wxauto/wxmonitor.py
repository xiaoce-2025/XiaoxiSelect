from wxauto4 import WeChat
wx = WeChat()
wx.SendMsg("冷阳","[系统自检]信息发送测试")
wx.StopListening()