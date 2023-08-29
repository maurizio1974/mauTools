import os
import hou


def denoise():
    base_render_dir = "/jobs/NYAD/sw1_104_1100/CG/CG_sw1_104_1100_lighting_environment_ocean_L010_BEAUTY_v042"
    channels = sorted(os.listdir(base_render_dir))
    xpos = 0
    ypos = 0
    channel_nodes = []
    # node_loc = "/img/img2"
    # MAKE THE IMAGE NETWORK NODE THAT WILL HOLD THE NODES
    shot = base_render_dir.split('/')[-1]
    denoise_name = shot + '_denoise'
    img = hou.node('/img/' + denoise_name)
    if not img:
        img = hou.node('/img').createNode('img', denoise_name)
    node_loc = img.path()
    # FIRST MERGE
    merge_node = hou.node(node_loc).createNode("merge", node_name="merge_channels")
    merge_node.setPosition(((len(channels)),ypos))
    ypos = ypos - 2
    # OPENNING THE OVERSCAN
    overscan_read = hou.node(node_loc).createNode('window', 'overscan_in')
    overscan_read.setParms({'window': 0, 'units': 1})
    overscan_read.setPosition(((len(channels)),ypos))
    overscan_read.setInput(0, merge_node, 0)
    ypos = ypos - 2
    # DENOISE NODE
    aidenoise_node = hou.node(node_loc).createNode("aidenoise", node_name="aidenoise_channels")
    aidenoise_node.setPosition(((len(channels)),ypos))
    aidenoise_node.setInput(0, overscan_read)
    aidenoise_node.parm("pscope").set("*")
    ypos = ypos - 2
    # RESTORE OVERSCAN
    overscan_restore = hou.node(node_loc).createNode('window', 'overscan_out')
    overscan_restore.setParms({'window': 0, 'units': 1})
    overscan_restore.setInput(0, aidenoise_node, 0)
    overscan_restore.setPosition(((len(channels)),ypos))
    ypos = ypos - 2
    for channel in channels:
        indir  = os.path.join(base_render_dir, channel)
        for render_path, render_dirs, render_files in os.walk(indir):
            for x, render_file in enumerate(render_files):
                render_path_new = render_path.replace('_L010_', '_DENOISED_L010_')
                render_file_new = render_file.replace('_L010_', '_DENOISED_L010_')
                infile = os.path.join(render_path, render_file)
                infile = infile.split(".")[0] + ".$F4.exr"
                outfile = os.path.join(render_path_new, render_file_new)
                outfile = outfile.split(".")[0] + ".$F4.exr"
                file_node = hou.node(node_loc).createNode("file", node_name="read_" + channel)
                file_node.parm("filename1").set(infile)
                file_node.setPosition((xpos,(ypos + 10)))
                merge_node.setInput(channels.index(channel), file_node)
                file_out_node = hou.node(node_loc).createNode("rop_comp", node_name="write_" + channel)
                file_out_node.setPosition((xpos,(ypos - 2)))
                file_out_node.setInput(0, overscan_restore)
                file_out_node.parm("copoutput").set(outfile)
                if channel == "beauty":
                    imageY = file_node.parm('size1').eval()
                    imageX = file_node.parm('size2').eval()
                    of1 = imageY*5/100
                    of2 = imageX*5/100
                    ha2 = imageY + (imageY*10/100)
                    va2 = imageX + (imageX*10/100)
                    overscan_read.setParms({'harea2': ha2, 'varea2': va2, 'offset1': of1, 'offset2': of2})

                    ofr1 = (imageY*5/100) * -1
                    ofr2 = (imageX*5/100) * -1
                    har2 = imageY
                    var2 = imageX
                    overscan_restore.setParms({'harea2': har2, 'varea2': var2, 'offset1': ofr1, 'offset2': ofr2})
                    print imageY, imageX
                if channel == "beauty":
                    file_out_node.parm("scopeplanes").set("C A")
                else:
                    file_out_node.parm("scopeplanes").set("__" + channel)
                xpos = xpos + 2
                print 'Working on', channel
                break