# Discord_MCmanager

DiscordBOTでMinecraftサーバの起動-停止を制御するコード。

Discordサーバ内のメッセージに応答してMinecraftサーバはscreen内で実行されます。サーバ内のユーザ人数はRCONで監視されユーザログアウトから2分後に自動的にシャットダウンされます。[DiscordSRV](https://github.com/DiscordSRV/DiscordSRV)などを利用するとロビーサーバ内からのチャットでサーバを起動できるのでおすすめです。

[bungeecord](https://minecraftjapan.miraheze.org/wiki/%E3%83%84%E3%83%BC%E3%83%AB/BungeeCord) [spawnonlogin](https://www.spigotmc.org/resources/spawn-on-login.8099/reviews) [Advanced-Portals](https://www.spigotmc.org/resources/advanced-portals.14356/)  [HolographicDisplays](https://dev.bukkit.org/projects/holographic-displays) などを導入するのをおすすめします。

運用例↓↓

<img src="img/構成.png" width="800">
