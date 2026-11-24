from ngSkinTools2 import signal
from ngSkinTools2.api import influence_names
from ngSkinTools2.api.influenceMapping import InfluenceInfo
from ngSkinTools2.api.layers import Layer
from ngSkinTools2.api.log import getLogger
from ngSkinTools2.api.pyside import QtCore, QtGui, QtWidgets
from ngSkinTools2.api.target_info import list_influences
from ngSkinTools2.ui import actions, qt
from ngSkinTools2.ui.layout import scale_multiplier
from ngSkinTools2.ui.options import Config, config

log = getLogger("influencesView")
_ = Layer  # only imported for type reference


def build_used_influences_action(parent):
    def toggle():
        config.influences_show_used_influences_only.set(not config.influences_show_used_influences_only())

    result = actions.define_action(
        parent,
        "Used Influences Only",
        callback=toggle,
        tooltip="If enabled, influences view will only show influences that have weights on current layer",
    )

    @signal.on(config.influences_show_used_influences_only.changed, qtParent=parent)
    def update():
        result.setChecked(config.influences_show_used_influences_only())

    result.setCheckable(True)
    update()
    return result


def build_set_influences_sorted_action(parent):
    from ngSkinTools2.ui import actions

    def toggle():
        new_value = Config.InfluencesSortDescending
        if config.influences_sort() == new_value:
            new_value = Config.InfluencesSortUnsorted
        config.influences_sort.set(new_value)

    result = actions.define_action(
        parent,
        "Show influences sorted",
        callback=toggle,
        tooltip="Sort influences by name",
    )

    @signal.on(config.influences_show_used_influences_only.changed, qtParent=parent)
    def update():
        result.setChecked(config.influences_sort() == Config.InfluencesSortDescending)

    result.setCheckable(True)
    update()
    return result


icon_mask = QtGui.QIcon(":/blendColors.svg")
icon_dq = QtGui.QIcon(":/rotate_M.png")
icon_joint = QtGui.QIcon(":/joint.svg")
icon_joint_disabled = qt.image_icon("joint_disabled.png")
icon_transform = QtGui.QIcon(":/cube.png")
icon_transform_disabled = qt.image_icon("cube_disabled.png")


def build_view(parent, actions, session, filter):
    """
    :param parent: ui parent
    :type actions: ngSkinTools2.ui.actions.Actions
    :type session: ngSkinTools2.ui.session.Session
    :type filter: InfluenceNameFilter
    """

    icon_locked = QtGui.QIcon(":/Lock_ON.png")
    icon_unlocked = QtGui.QIcon(":/Lock_OFF_grey.png")

    id_role = QtCore.Qt.UserRole + 1
    item_size_hint = QtCore.QSize(25 * scale_multiplier, 25 * scale_multiplier)

    def get_item_id(item):
        if item is None:
            return None
        return item.data(0, id_role)

    tree_items = {}

    def build_items(view, items, layer):
        # type: (QtWidgets.QTreeWidget, list[InfluenceInfo], Layer) -> None
        is_group_layer = layer is not None and layer.num_children != 0

        def rebuild_buttons(item, item_id, buttons):
            bar = QtWidgets.QToolBar(parent=parent)
            bar.setMovable(False)
            bar.setIconSize(QtCore.QSize(13 * scale_multiplier, 13 * scale_multiplier))

            def add_or_remove(input_list, items, should_add):
                if should_add:
                    return list(input_list) + list(items)
                return [i for i in input_list if i not in items]

            def lock_unlock_handler(lock):
                def handler():
                    targets = layer.paint_targets
                    if item_id not in targets:
                        targets = (item_id,)

                    layer.locked_influences = add_or_remove(layer.locked_influences, targets, lock)
                    log.info("updated locked influences to %r", layer.locked_influences)
                    session.events.influencesListUpdated.emit()

                return handler

            if "unlocked" in buttons:
                a = bar.addAction(icon_unlocked, "Toggle locked/unlocked")
                qt.on(a.triggered)(lock_unlock_handler(True))

            if "locked" in buttons:
                a = bar.addAction(icon_locked, "Toggle locked/unlocked")
                qt.on(a.triggered)(lock_unlock_handler(False))

            view.setItemWidget(item, 1, bar)

        selected_ids = []
        if session.state.currentLayer.layer:
            selected_ids = session.state.currentLayer.layer.paint_targets
        current_id = None if not selected_ids else selected_ids[0]

        with qt.signals_blocked(view):
            tree_items.clear()
            tree_root = view.invisibleRootItem()

            item_index = 0
            for item_id, displayName, icon, buttons in wanted_tree_items(
                items=items,
                include_dq_item=session.state.skin_cluster_dq_channel_used,
                is_group_layer=is_group_layer,
                layer=layer,
                config=config,
                filter=filter,
            ):
                if item_index >= tree_root.childCount():
                    item = QtWidgets.QTreeWidgetItem([displayName])
                else:
                    item = tree_root.child(item_index)
                    item.setText(0, displayName)

                item.setData(0, id_role, item_id)
                item.setIcon(0, icon)
                item.setSizeHint(0, item_size_hint)
                tree_root.addChild(item)

                tree_items[item_id] = item
                if item_id == current_id:
                    view.setCurrentItem(item, 0, QtCore.QItemSelectionModel.NoUpdate)
                item.setSelected(item_id in selected_ids)

                rebuild_buttons(item, item_id, buttons)

                item_index += 1

            while item_index < tree_root.childCount():
                tree_root.removeChild(tree_root.child(item_index))

    view = QtWidgets.QTreeWidget(parent)
    view.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
    view.setUniformRowHeights(True)
    view.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
    view.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
    actions.addInfluencesActions(view)
    view.addAction(actions.separator(parent, "View Options"))
    view.addAction(actions.show_used_influences_only)
    view.addAction(actions.set_influences_sorted)
    view.setIndentation(10 * scale_multiplier)
    view.header().setStretchLastSection(False)
    view.header().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)

    view.setHeaderLabels(["Influences", ""])
    view.header().setSectionResizeMode(1, QtWidgets.QHeaderView.Fixed)
    view.setColumnWidth(1, 25 * scale_multiplier)

    # view.setHeaderHidden(True)
    def refresh_items():
        items = list_influences(session.state.currentLayer.selectedSkinCluster)

        def sort_func(a):
            """
            :type a: InfluenceInfo
            """
            return a.name

        # items = sorted(items, key=sort_func)
        build_items(view, items, session.state.currentLayer.layer)

    @signal.on(
        filter.changed,
        config.influences_show_used_influences_only.changed,
        config.influences_sort.changed,
        session.events.influencesListUpdated,
    )
    def filter_changed():
        refresh_items()

    @signal.on(session.events.currentLayerChanged, qtParent=view)
    def current_layer_changed():
        if not session.state.currentLayer.layer:
            build_items(view, [], None)
        else:
            log.info("current layer changed to %s", session.state.currentLayer.layer)
            refresh_items()
            current_influence_changed()

    @signal.on(session.events.currentInfluenceChanged, qtParent=view)
    def current_influence_changed():
        if session.state.currentLayer.layer is None:
            return

        log.info("current influence changed - updating item selection")
        with qt.signals_blocked(view):
            targets = session.state.currentLayer.layer.paint_targets
            first = True
            for tree_item in tree_items.values():
                selected = get_item_id(tree_item) in targets
                if selected and first:
                    view.setCurrentItem(tree_item, 0, QtCore.QItemSelectionModel.NoUpdate)
                first = False
                tree_item.setSelected(selected)

    @qt.on(view.currentItemChanged)
    def current_item_changed(curr, prev):
        if curr is None:
            return

        if session.state.selectedSkinCluster is None:
            return

        if not session.state.currentLayer.layer:
            return

        log.info("focused item changed: %r", get_item_id(curr))
        sync_paint_targets_to_selection()

    @qt.on(view.itemSelectionChanged)
    def sync_paint_targets_to_selection():
        log.info("syncing paint targets")
        selected_ids = [get_item_id(item) for item in view.selectedItems()]
        selected_ids = [i for i in selected_ids if i is not None]

        current_item = view.currentItem()
        if current_item and current_item.isSelected():
            # move id of current item to front, if it's selected
            item_id = get_item_id(current_item)
            selected_ids.remove(item_id)
            selected_ids = [item_id] + selected_ids

        if session.state.currentLayer.layer:
            session.state.currentLayer.layer.paint_targets = selected_ids

    current_layer_changed()

    return view


def get_icon(influence, is_joint):
    if influence.used:
        return icon_joint if is_joint else icon_transform
    return icon_joint_disabled if is_joint else icon_transform_disabled


def wanted_tree_items(
    layer,
    config,
    is_group_layer,
    include_dq_item,
    filter,
    items,
):
    """

    :type items: list[InfluenceInfo]
    """

    if layer is None:
        return

    # calculate "used" regardless as we're displaying it visually even if "show used influences only" is toggled off
    used = set((layer.get_used_influences() or []))
    locked = set((layer.locked_influences or []))
    for i in items:
        i.used = i.logicalIndex in used
        i.locked = i.logicalIndex in locked

    if config.influences_show_used_influences_only() and layer is not None:
        items = [i for i in items if i.used]

    if is_group_layer:
        items = []

    yield "mask", "[Mask]", icon_mask, []
    if not is_group_layer and include_dq_item:
        yield "dq", "[DQ Weights]", icon_dq, []

    names = influence_names.unique_names([i.path_name() for i in items])
    for i, name in zip(items, names):
        i.unique_name = name

    if config.influences_sort() == Config.InfluencesSortDescending:
        items = list(sorted(items, key=lambda i: i.unique_name))

    for i in items:
        is_joint = i.path is not None
        if filter.is_match(i.path_name()):
            yield i.logicalIndex, i.unique_name, get_icon(i, is_joint), ["locked" if i.locked else "unlocked"]
