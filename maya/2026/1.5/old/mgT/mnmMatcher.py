from maya import cmds, mel



def mMatcher(bt):
	sel = cmds.ls(sl=True)
	if not sel:
		cmds.confirmDialog(t='Selection Error', m='Select one object and all those you want to match to it')
		return
	if len(sel) < 1:
		cmds.confirmDialog(t='Selection Error', m='Select at least two objects')
		return
	ui = [
		'INcheckBttn', 'buttonTR', 'trsXcheckbox', 'trsYcheckbox', 'trsZcheckbox',
		'buttonRO', 'rotXcheckbox', 'rotYcheckbox', 'rotZcheckbox', 'buttonSO',
		'scaXcheckbox', 'scaYcheckbox', 'scaZcheckbox', 'buttonTRO', 'buttonCENT']

	INcheckBttn = cmds.checkBox('INcheckBttn', q=True, v=True)
	trsXcheckbox = cmds.checkBox('trsXcheckbox', q=True, v=True)
	trsYcheckbox = cmds.checkBox('trsYcheckbox', q=True, v=True)
	trsZcheckbox = cmds.checkBox('trsZcheckbox', q=True, v=True)
	rotXcheckbox = cmds.checkBox('rotXcheckbox', q=True, v=True)
	rotYcheckbox = cmds.checkBox('rotYcheckbox', q=True, v=True)
	rotZcheckbox = cmds.checkBox('rotZcheckbox', q=True, v=True)
	scaXcheckbox = cmds.checkBox('scaXcheckbox', q=True, v=True)
	scaYcheckbox = cmds.checkBox('scaYcheckbox', q=True, v=True)
	scaZcheckbox = cmds.checkBox('scaZcheckbox', q=True, v=True)
	
	if INcheckBttn:
		sel.reverse()
	base_cmd = f'cmds.matchTransform("{sel[0]}", '
	for s in sel:
		if s != sel[0]:
			base_cmd += f'"{s}", '
	if bt == 'buttonTR':
		base_cmd += f'px={trsXcheckbox}, py={trsYcheckbox}, pz={trsZcheckbox}'
	elif bt == 'buttonRO':
		base_cmd += f'rx={rotXcheckbox}, ry={rotYcheckbox}, rz={rotZcheckbox}'
	elif bt == 'buttonSO':
		base_cmd += f'sx={scaXcheckbox}, sy={scaYcheckbox}, sz={scaZcheckbox}'
	elif bt == 'buttonTRO':
		base_cmd += f'px={trsXcheckbox}, py={trsYcheckbox}, pz={trsZcheckbox},'
		base_cmd += f'rx={rotXcheckbox}, ry={rotYcheckbox}, rz={rotZcheckbox},'
		base_cmd += f'sx={scaXcheckbox}, sy={scaYcheckbox}, sz={scaZcheckbox}'
	base_cmd += ')'
	print(base_cmd)
	exec(base_cmd)