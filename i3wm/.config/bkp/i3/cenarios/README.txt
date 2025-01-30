🚀️ CRIAR CENÁRIO

i3-save-tree --workspace X > ~/.config/i3/cenarios/MEUlayout.json

🚀️ EDITANDO LAYOUT ==> MEUlayout.json

nano ~/.config/i3/cenarios/MEUlayout.json

  {
  // "class": "^Gedit$",
  // "instance": "^gedit$",
  // "machine": "^arch$",
  // "title": "^README\\.txt\\ \\(\\~\\/\\.config\\/i3\\/cenarios\\)\\ \\-\\ gedit$"
  }

Remove os comentários // dos programas que estavam abertos, nos atributos "class" e "instance"
Remove demais atributos, lembrando que a ultima linha entre as chaves{} não pode ter virgula(;)

🚀️ TESTAR CENÁRIO NO TERMINAL

i3-msg "workspace X; append_layout ~/.config/i3/cenarios/MEUlayout.json; exec firefox; exec geany; exec nemo; exec tilix"

🚀️ SETAR ATALHOS NO CONFIG NO I3 CONFIG

START IN CURRENT WORKSPACE
$sup+X append_layout ~/.config/i3/cenarios/MEUlayout.json; $exe firefox; $exe geany; $exe nemo; $exe tilix"

START IN A SPECIFIC WORKSPACE
$sup+X workspace X; append_layout ~/.config/i3/cenarios/MEUlayout.json; $exe firefox; $exe geany; $exe nemo; $exe tilix"

