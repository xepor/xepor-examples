# Removing Krisp online license check

[Krisp](https://krisp.ai/) is an Windows desktop application written in C#.

> Krisp is an AI-powered noise cancelling app that removes background noise and echo during online calls in real time

This example is a script used together with a slightly modified Krisp client application, to get over the license check which is completely unnecessary for an offline application.

In detail, it *patched* some of the JSON fields used for license verification, and leave everything else intact (the authorization, personal settings). I'm just too lazy to reverse engineer everything.

The script was written years ago, it may or may not compatible with later versions of Krisp client and mitmproxy. Create an [Issue](https://github.com/xepor/xepor-examples/issues) if you have any problem or suggestions.

For detailed analysis and steps to reproduce, check my blog post (currently in Chinese only):

[快速搭建Mock API进行应用安全测试——以某音频处理软件为例 - 兔比妙妙屋](https://blog.rabit.pw/2020/mitmproxy-mock-api/)
