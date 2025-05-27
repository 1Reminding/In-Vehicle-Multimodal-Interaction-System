// 文件：Main.qml
import QtQuick 2.15
import QtQuick.Window 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

ApplicationWindow {
    id: window
    width: 1280
    height: 720
    visible: true
    title: "车载多模态系统"
    color: "#1E1E1E"

    //全局变量
    property string currentMusicImage: "assets/empty_music.png"
    property string driverState: "assets/safe.png"
    property string musicTitle: "暂无音乐播放"
    property string weatherTemperature: "???"
    property string weatherImage: ""
    property string acImage: "assets/close.png"
    property string driverStateMessage: "驾驶员状态正常"
    property string acStateText: "关闭"


    function setMusicImage(path) {
        //stackView.currentItem.homeMusicImageRef.width += 1  
        //stackView.currentItem.homeMusicImageRef.height += 1
        Qt.callLater(() => {
            currentMusicImage = path
            //stackView.currentItem.homeMusicImageRef.width -= 1
            //stackView.currentItem.homeMusicImageRef.height -= 1
        })
    }

    // 动态时间属性
    property string currentTime: Qt.formatDateTime(new Date(), "yyyy年MM月dd日 hh:mm:ss")
    property string currentDay: Qt.formatDateTime(new Date(), "dddd")

    // 每秒更新日期和时间
    Timer {
        interval: 1000
        running: true
        repeat: true
        onTriggered: {
            var now = new Date()
            currentTime = Qt.formatDateTime(now, "yyyy年MM月dd日 hh:mm:ss")
            currentDay = Qt.formatDateTime(now, "dddd")
        }
    }

    Connections {
        target: UIBackend
        function onCommandIssued(cmd) {
            console.log("收到后端命令：", cmd)
            switch (cmd) {
            case "PlayMusic":              
                setMusicImage("assets/music.png")
                musicTitle = "南开校歌"
                break
            case "TurnOnAC":
                acImage = "assets/open.png"
                acStateText = "23°C  自动"
                break
            case "distract":
                driverState = "assets/dangerous.png"
                driverStateMessage = "请注意！驾驶员注意力分散"
                stackView.replace(driverPage)  // 强制跳转到驾驶员状态页面
                break
            case "NoticeRoad":
                driverState = "assets/safe.png"
                driverStateMessage = "驾驶员状态正常"
                stackView.replace(homePage)  // 状态恢复后自动跳回主页
                break
            }
        }
    }

    Connections {
        target: UIBackend
        function onWeatherUpdated(temp) {
            console.log("收到天气更新:", temp)
            weatherTemperature = temp
            if (temp.indexOf("晴天") !== -1 || temp.indexOf("晴") !== -1) {
                weatherImage = "assets/sun.png"
            }
            if (temp.indexOf("雨") !== -1) {
                weatherImage = "assets/rain.png"
            }
            if (temp.indexOf("云") !== -1) {
                weatherImage = "assets/cloud.png"
            }
        }
    }

    // 移除默认标题栏
    flags: Qt.Window | Qt.FramelessWindowHint
    
    // 自定义标题栏
    Rectangle {
        id: customTitleBar
        width: parent.width
        height: 36
        color: "#2E2E2E"  // 直接使用应用背景的颜色值，确保一致
        
        MouseArea {
            id: titleBarMouseArea
            anchors.fill: parent
            property point clickPos: "0,0"
            
            onPressed: {
                clickPos = Qt.point(mouse.x, mouse.y)
            }
            
            onPositionChanged: {
                if (pressed) {
                    var delta = Qt.point(mouse.x-clickPos.x, mouse.y-clickPos.y)
                    window.x += delta.x
                    window.y += delta.y
                }
            }
        }
        
        // 标题
        Row {
            anchors.left: parent.left
            anchors.leftMargin: 10
            anchors.verticalCenter: parent.verticalCenter
            spacing: 8
            
            Image {
                source: "assets/car_icon.png"  // 使用适当的应用图标
                width: 28
                height: 28
                anchors.verticalCenter: parent.verticalCenter
            }
            
            Text {
                text: "车载多模态系统"
                color: "#FFFFFF"
                font.pixelSize: 14
                anchors.verticalCenter: parent.verticalCenter
            }
        }
        
        // 窗口控制按钮
        Row {
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            
            // 最小化按钮
            Rectangle {
                width: 46
                height: parent.height
                color: minimizeArea.containsMouse ? "#363636" : "transparent"
                
                Text {
                    text: "—"
                    anchors.centerIn: parent
                    color: "#FFFFFF"
                }
                
                MouseArea {
                    id: minimizeArea
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: window.showMinimized()
                }
            }
            
            // 最大化按钮
            Rectangle {
                width: 46
                height: parent.height
                color: maximizeArea.containsMouse ? "#363636" : "transparent"
                
                Text {
                    text: "□"
                    anchors.centerIn: parent
                    color: "#FFFFFF"
                }
                
                MouseArea {
                    id: maximizeArea
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: {
                        if (window.visibility === Window.Maximized) {
                            window.showNormal()
                        } else {
                            window.showMaximized()
                        }
                    }
                }
            }
            
            // 关闭按钮
            Rectangle {
                width: 46
                height: parent.height
                color: closeArea.containsMouse ? "#E81123" : "transparent"
                
                Text {
                    text: "✕"
                    anchors.centerIn: parent
                    color: "#FFFFFF"
                }
                
                MouseArea {
                    id: closeArea
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: window.close()
                }
            }
        }
    }

    // 顶部导航栏
    Rectangle {
        id: headerRect
        width: parent.width
        height: 50
        anchors.top: customTitleBar.bottom
        color: "#2E2E2E"

        RowLayout {
            anchors.fill: parent
            anchors.margins: 10
            spacing: 20

            //菜单按钮：扩展？
            //ToolButton {
            //    icon.name: "menu"
            //    onClicked: sidebar.visible = !sidebar.visible
            //    Layout.alignment: Qt.AlignVCenter
            //}
            Label {
                text: currentTime
                font.pixelSize: 18
                color: "white"
                Layout.alignment: Qt.AlignVCenter
            }
            Item { Layout.fillWidth: true }
            Label {
                text: currentDay
                font.pixelSize: 18
                color: "white"
                Layout.alignment: Qt.AlignVCenter
            }
        }
    }

    // 左侧常驻侧边栏
    Rectangle {
        id: sidebar
        width: 200
        anchors.top: headerRect.bottom
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        color: "#2E2E2E"
        z: 1

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 10
            spacing: 50

            Button {
                id: homeButton
                text: "主页"
                font.pixelSize: 20
                implicitWidth: 150
                implicitHeight: 50
                Layout.alignment: Qt.AlignHCenter

                background: Rectangle {
                    radius: 8
                    color: homeButton.down ? "#505050" : (homeButton.hovered ? "#3E3E3E" : "#2E2E2E")
                    border.color: "#AAAAAA"
                }

                contentItem: Item {
                    anchors.fill: parent

                    Row {
                        anchors.centerIn: parent
                        spacing: 10

                        Image {
                            source: "assets/home_icon.png"
                            width: 24
                            height: 24
                            fillMode: Image.PreserveAspectFit
                            smooth: true
                            anchors.verticalCenter: parent.verticalCenter
                        }

                        Text {
                            text: homeButton.text
                            color: "white"
                            font.pixelSize: 18
                            anchors.verticalCenter: parent.verticalCenter
                        }
                    }
                }


    onClicked: stackView.replace(homePage)
}


            Button {
                id: musicButton
                text: "音乐"
                font.pixelSize: 20
                implicitWidth: 150
                implicitHeight: 50
                Layout.alignment: Qt.AlignHCenter

                background: Rectangle {
                    radius: 8
                    color: musicButton.down ? "#505050" : (musicButton.hovered ? "#3E3E3E" : "#2E2E2E")
                    border.color: "#AAAAAA"
                }

                contentItem: Item {
                    anchors.fill: parent

                    Row {
                        anchors.centerIn: parent
                        spacing: 10

                        Image {
                            source: "assets/music_icon.png"
                            width: 24
                            height: 24
                            fillMode: Image.PreserveAspectFit
                            smooth: true
                            anchors.verticalCenter: parent.verticalCenter
                        }

                        Text {
                            text: musicButton.text
                            color: "white"
                            font.pixelSize: 18
                            anchors.verticalCenter: parent.verticalCenter
                        }
                    }
                }

                onClicked: stackView.replace(musicPage)
            }


            // 在音乐按钮后面，exitButton前面添加
            Button {
                id: driverButton
                text: "驾驶员"
                font.pixelSize: 20
                implicitWidth: 150
                implicitHeight: 50
                Layout.alignment: Qt.AlignHCenter

                background: Rectangle {
                    radius: 8
                    color: driverButton.down ? "#505050" : (driverButton.hovered ? "#3E3E3E" : "#2E2E2E")
                    border.color: "#AAAAAA"
                }

                contentItem: Item {
                    anchors.fill: parent

                    Row {
                        anchors.centerIn: parent
                        spacing: 10

                        Image {
                            source: "assets/driver.png"
                            width: 24
                            height: 24
                            fillMode: Image.PreserveAspectFit
                            smooth: true
                            anchors.verticalCenter: parent.verticalCenter
                        }

                        Text {
                            text: driverButton.text
                            color: "white"
                            font.pixelSize: 18
                            anchors.verticalCenter: parent.verticalCenter
                        }
                    }
                }

                onClicked: stackView.replace(driverPage)
            }


            // 在驾驶员按钮后面，设置按钮前面添加
            Button {
                id: acButton
                text: "空调"
                font.pixelSize: 20
                implicitWidth: 150
                implicitHeight: 50
                Layout.alignment: Qt.AlignHCenter

                background: Rectangle {
                    radius: 8
                    color: acButton.down ? "#505050" : (acButton.hovered ? "#3E3E3E" : "#2E2E2E")
                    border.color: "#AAAAAA"
                }

                contentItem: Item {
                    anchors.fill: parent

                    Row {
                        anchors.centerIn: parent
                        spacing: 10

                        Image {
                            source: "assets/acButton.png"
                            width: 24
                            height: 24
                            fillMode: Image.PreserveAspectFit
                            smooth: true
                            anchors.verticalCenter: parent.verticalCenter
                        }

                        Text {
                            text: acButton.text
                            color: "white"
                            font.pixelSize: 18
                            anchors.verticalCenter: parent.verticalCenter
                        }
                    }
                }

                onClicked: stackView.replace(acPage)
            }


            // 在驾驶员按钮后面，exitButton前面添加
            Button {
                id: settingsButton
                text: "设置"
                font.pixelSize: 20
                implicitWidth: 150
                implicitHeight: 50
                Layout.alignment: Qt.AlignHCenter

                background: Rectangle {
                    radius: 8
                    color: settingsButton.down ? "#505050" : (settingsButton.hovered ? "#3E3E3E" : "#2E2E2E")
                    border.color: "#AAAAAA"
                }

                contentItem: Item {
                    anchors.fill: parent

                    Row {
                        anchors.centerIn: parent
                        spacing: 10

                        Image {
                            source: "assets/set.png"
                            width: 24
                            height: 24
                            fillMode: Image.PreserveAspectFit
                            smooth: true
                            anchors.verticalCenter: parent.verticalCenter
                        }

                        Text {
                            text: settingsButton.text
                            color: "white"
                            font.pixelSize: 18
                            anchors.verticalCenter: parent.verticalCenter
                        }
                    }
                }

                onClicked: stackView.replace(settingsPage)
            }


            // 添加退出按钮
            Item { Layout.fillHeight: true } // 弹性空间，将退出按钮推到底部
            
            Button {
                id: exitButton
                text: "退出"
                font.pixelSize: 20
                implicitWidth: 150
                implicitHeight: 50
                Layout.alignment: Qt.AlignHCenter
                Layout.bottomMargin: 20

                background: Rectangle {
                    radius: 8
                    color: exitButton.down ? "#505050" : (exitButton.hovered ? "#3E3E3E" : "#2E2E2E")
                    border.color: "#AAAAAA"
                }

                contentItem: Item {
                    anchors.fill: parent

                    Row {
                        anchors.centerIn: parent
                        spacing: 10

                        Image {
                            source: "assets/out_icon.png"
                            width: 24
                            height: 24
                            fillMode: Image.PreserveAspectFit
                            smooth: true
                            anchors.verticalCenter: parent.verticalCenter
                        }

                        Text {
                            text: exitButton.text
                            color: "white"
                            font.pixelSize: 18
                            anchors.verticalCenter: parent.verticalCenter
                        }
                    }
                }

                onClicked: window.close()
            }

        }
    }

    // 主内容区
    StackView {
        id: stackView
        z: 0
        anchors {
            top: headerRect.bottom
            left: sidebar.right
            right: parent.right
            bottom: parent.bottom
        }
        initialItem: homePage

        
    }

    // —— 主页 页面 —— //
    Component {
        id: homePage
        Page {
            id: homePageRoot

            property alias homeMusicImageRef: homeMusicImage

            background: Rectangle { color: "#1E1E2D" }

            GridLayout {
                anchors.fill: parent
                anchors.margins: 20
                columns: 2
                rowSpacing: 20
                columnSpacing: 20

                // 天气卡片
                Rectangle {
                    id: weatherCard
                    radius: 10
                    color: "#262626"
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    height: 150

                    // 使用 Item 包裹自由布局
                    Item {
                        anchors.fill: parent

                        // 左上角天气信息
                        Column {
                            anchors.top: parent.top
                            anchors.left: parent.left
                            anchors.margins: 10
                            spacing: 6
                            Label {
                                text: weatherTemperature  // 例如 "21°C"
                                font.pixelSize: 24
                                color: "white"
                            }
                        }

                        // 居中图片
                        Image {
                            source: weatherImage
                            fillMode: Image.PreserveAspectFit
                            width: parent.width * 0.3
                            height: width
                            anchors.centerIn: parent
                        }
                    }
                }


                // 音乐卡片（可点击）
                Rectangle {
                    id: musicCard
                    radius: 10
                    color: "#262626"
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    height: 150

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 10

                        Label { text: "音乐"; font.pixelSize: 20; color: "white" }
                        Item {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            Layout.alignment: Qt.AlignHCenter | Qt.AlignVCenter

                            Image {
                                id: homeMusicImage
                                objectName: "homeMusicImage"
                                source: currentMusicImage
                                fillMode: Image.PreserveAspectFit
                                width: parent.width * 0.8
                                height: parent.height * 0.8
                                anchors.centerIn: parent
                            }
                        }

                    }

                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: stackView.replace(musicPage)
                        onEntered: musicCard.color = "#3A3A3A"
                        onExited: musicCard.color = "#262626"
                    }
                }

                 // 空调卡片
                Rectangle {
                    id: acCard
                    radius: 10
                    color: "#262626"
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    height: 150

                    // 使用 Item 包裹自由布局
                    Item {
                        anchors.fill: parent

                        // 左上角空调信息
                        Column {
                            anchors.top: parent.top
                            anchors.left: parent.left
                            anchors.margins: 10
                            spacing: 6
                            
                            Label { 
                                text: "空调"
                                font.pixelSize: 20
                                color: "white" 
                            }
                            
                            Label { 
                                text: acStateText
                                color: "white" 
                            }
                        }

                        // 居中图片
                        Image {
                            source: acImage
                            fillMode: Image.PreserveAspectFit
                            width: parent.width * 0.3
                            height: width
                            anchors.centerIn: parent
                        }
                    }

                    // 添加鼠标区域使卡片可点击
                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: stackView.replace(acPage)
                        onEntered: acCard.color = "#3A3A3A"
                        onExited: acCard.color = "#262626"
                    }
                }

                // 驾驶员状态卡片
                Rectangle {
                    id: driverCard
                    radius: 10
                    color: "#262626"
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    height: 150

                    // 使用 anchors 和 Layout 结合排布
                    Item {
                        anchors.fill: parent

                        // 左上角标题
                        Label {
                            text: "驾驶员状态"
                            font.pixelSize: 20
                            color: "white"
                            anchors.top: parent.top
                            anchors.left: parent.left
                            anchors.margins: 10
                        }

                        // 居中的图片
                        Image {
                            source: driverState
                            fillMode: Image.PreserveAspectFit
                            anchors.centerIn: parent
                            width: parent.width * 0.4
                            height: width
                        }
                    }

                    // 添加鼠标区域使卡片可点击
                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: stackView.replace(driverPage)
                        onEntered: driverCard.color = "#3A3A3A"
                        onExited: driverCard.color = "#262626"
                    }
                }

            }
        }
    }

    // —— 音乐 页面 —— //
    Component {
        id: musicPage
        Page {
            property bool isPlaying: false

            background: Rectangle { color: "#1E1E2D" }

            ColumnLayout {
                anchors.centerIn: parent
                anchors.margins: 20
                spacing: 30

                Image {
                    source: currentMusicImage
                    fillMode: Image.PreserveAspectFit
                    width: window.width * 0.4
                    height: width
                    Layout.alignment: Qt.AlignHCenter
                }

                // 居中文本标签
                Item {
                    Layout.fillWidth: true
                    Label {
                        anchors.horizontalCenter: parent.horizontalCenter
                        text: musicTitle
                        font.pixelSize: 20
                        color: "white"
                    }
                }

                

                ToolButton {
                    id: playPauseButton
                    Layout.alignment: Qt.AlignHCenter
                    width: 40
                    height: 40

                    // 使用图像作为按钮内容
                    contentItem: Image {
                        id: playPauseIcon
                        source: isPlaying ? "assets/pause.png" : "assets/play.png"
                        fillMode: Image.PreserveAspectFit
                        anchors.centerIn: parent
                        width: parent.width
                        height: parent.height
                    }

                    onClicked: {
                        isPlaying = !isPlaying
                        console.log("切换状态，当前图标:", playPauseIcon.source)
                    }
                }
            }
        }
    }

    // —— 驾驶员页面 —— //
    Component {
        id: driverPage
        Page {
            background: Rectangle { color: "#1E1E2D" }

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 20
                spacing: 30

                Item {
                    Layout.fillWidth: true
                    Layout.fillHeight: true

                    // 大尺寸的驾驶员状态图标
                    Image {
                        source: driverState
                        fillMode: Image.PreserveAspectFit
                        width: Math.min(parent.width, parent.height) * 0.8
                        height: width
                        anchors.centerIn: parent
                    }
                }

                // 底部状态栏
                Rectangle {
                    Layout.fillWidth: true
                    height: 60
                    color: "#262626"
                    radius: 8

                    Label {
                        anchors.centerIn: parent
                        text: driverStateMessage
                        font.pixelSize: 20
                        color: "white"
                    }
                }
            }
        }
    }


    // —— 设置页面 —— //
    Component {
        id: settingsPage
        Page {
            id: settingsPageRoot
            background: Rectangle { color: "#1E1E2D" }

            // 添加页面标题区域
            Rectangle {
                id: settingsHeaderBar
                anchors.top: parent.top
                anchors.left: parent.left
                anchors.right: parent.right
                height: 60
                color: "#1E1E2D"

                Label {
                    text: "系统设置"
                    font.pixelSize: 24
                    font.bold: true
                    color: "white"
                    anchors.centerIn: parent
                }
            }

            ScrollView {
                anchors.top: settingsHeaderBar.bottom
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                anchors.margins: 15
                clip: true
                
                ColumnLayout {
                    width: parent.width
                    spacing: 15
                    
                    // 音量控制组
                    Rectangle {
                        Layout.fillWidth: true
                        height: 80
                        color: "#262626"
                        radius: 10
                        
                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 15
                            spacing: 20
                            
                            // 图标
                            Rectangle {
                                width: 40
                                height: 40
                                radius: 20
                                color: "#333344"
                                
                                Text {
                                    text: "🔊"
                                    font.pixelSize: 20
                                    anchors.centerIn: parent
                                    color: "white"
                                }
                            }
                            
                            Label {
                                text: "音量"
                                font.pixelSize: 18
                                color: "white"
                                Layout.minimumWidth: 50
                            }
                            
                            Slider {
                                id: volumeSlider
                                Layout.fillWidth: true
                                from: 0
                                to: 100
                                value: 75
                                
                                background: Rectangle {
                                    x: volumeSlider.leftPadding
                                    y: volumeSlider.topPadding + volumeSlider.height / 2 - height / 2
                                    width: volumeSlider.availableWidth
                                    height: 6
                                    radius: 3
                                    color: "#3E3E3E"
                                    
                                    Rectangle {
                                        width: volumeSlider.visualPosition * parent.width
                                        height: parent.height
                                        color: "#4CAF50"
                                        radius: 3
                                    }
                                }
                                
                                handle: Rectangle {
                                    x: volumeSlider.leftPadding + volumeSlider.visualPosition * volumeSlider.availableWidth - width / 2
                                    y: volumeSlider.topPadding + volumeSlider.height / 2 - height / 2
                                    width: 20
                                    height: 20
                                    radius: 10
                                    color: volumeSlider.pressed ? "#f0f0f0" : "#f6f6f6"
                                    border.color: "#bbb"
                                    
                                    
                                }
                            }
                            
                            Label {
                                text: Math.round(volumeSlider.value) + "%"
                                font.pixelSize: 18
                                color: "white"
                                Layout.minimumWidth: 45
                                horizontalAlignment: Text.AlignRight
                            }
                        }
                    }
                    
                    // 亮度控制组
                    Rectangle {
                        Layout.fillWidth: true
                        height: 80
                        color: "#262626"
                        radius: 10
                        
                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 15
                            spacing: 20
                            
                            // 图标
                            Rectangle {
                                width: 40
                                height: 40
                                radius: 20
                                color: "#333344"
                                
                                Text {
                                    text: "☀️"
                                    font.pixelSize: 20
                                    anchors.centerIn: parent
                                    color: "white"
                                }
                            }
                            
                            Label {
                                text: "亮度"
                                font.pixelSize: 18
                                color: "white"
                                Layout.minimumWidth: 50
                            }
                            
                            Slider {
                                id: brightnessSlider
                                Layout.fillWidth: true
                                from: 10
                                to: 100
                                value: 80
                                
                                background: Rectangle {
                                    x: brightnessSlider.leftPadding
                                    y: brightnessSlider.topPadding + brightnessSlider.height / 2 - height / 2
                                    width: brightnessSlider.availableWidth
                                    height: 6
                                    radius: 3
                                    color: "#3E3E3E"
                                    
                                    Rectangle {
                                        width: brightnessSlider.visualPosition * parent.width
                                        height: parent.height
                                        color: "#FFC107"
                                        radius: 3
                                    }
                                }
                                
                                handle: Rectangle {
                                    x: brightnessSlider.leftPadding + brightnessSlider.visualPosition * brightnessSlider.availableWidth - width / 2
                                    y: brightnessSlider.topPadding + brightnessSlider.height / 2 - height / 2
                                    width: 20
                                    height: 20
                                    radius: 10
                                    color: brightnessSlider.pressed ? "#f0f0f0" : "#f6f6f6"
                                    border.color: "#bbb"
                                    
                                    
                                }
                            }
                            
                            Label {
                                text: Math.round(brightnessSlider.value) + "%"
                                font.pixelSize: 18
                                color: "white"
                                Layout.minimumWidth: 45
                                horizontalAlignment: Text.AlignRight
                            }
                        }
                    }
                    
                    // 主题选择组
                    Rectangle {
                        Layout.fillWidth: true
                        height: 80
                        color: "#262626"
                        radius: 10
                        
                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 15
                            spacing: 20
                            
                            // 图标
                            Rectangle {
                                width: 40
                                height: 40
                                radius: 20
                                color: "#333344"
                                
                                Text {
                                    text: "🎨"
                                    font.pixelSize: 20
                                    anchors.centerIn: parent
                                    color: "white"
                                }
                            }
                            
                            Label {
                                text: "主题"
                                font.pixelSize: 18
                                color: "white"
                                Layout.minimumWidth: 50
                            }
                            
                            Item { Layout.fillWidth: true }
                            
                            ComboBox {
                                id: themeComboBox
                                model: ["深色主题", "浅色主题", "蓝色主题"]
                                currentIndex: 0
                                width: 180
                                
                                contentItem: Text {
                                    leftPadding: 10
                                    text: themeComboBox.displayText
                                    color: "white"
                                    font.pixelSize: 16
                                    verticalAlignment: Text.AlignVCenter
                                }
                                
                                background: Rectangle {
                                    implicitWidth: 180
                                    implicitHeight: 40
                                    color: themeComboBox.pressed ? "#454550" : "#353540"
                                    radius: 5
                                    border.color: "#555560"
                                    border.width: 1
                                }
                                
                                popup: Popup {
                                    y: themeComboBox.height
                                    width: themeComboBox.width
                                    implicitHeight: contentItem.implicitHeight
                                    padding: 1
                                    
                                    contentItem: ListView {
                                        implicitHeight: contentHeight
                                        model: themeComboBox.popup.visible ? themeComboBox.delegateModel : null
                                        
                                        ScrollIndicator.vertical: ScrollIndicator { }
                                    }
                                    
                                    background: Rectangle {
                                        color: "#353540"
                                        border.color: "#555560"
                                        border.width: 1
                                        radius: 3
                                    }
                                }
                                
                                delegate: ItemDelegate {
                                    width: themeComboBox.width
                                    contentItem: Text {
                                        text: modelData
                                        color: "white"
                                        font.pixelSize: 16
                                        elide: Text.ElideRight
                                        verticalAlignment: Text.AlignVCenter
                                    }
                                    highlighted: themeComboBox.highlightedIndex === index
                                    
                                    background: Rectangle {
                                        color: highlighted ? "#454550" : "#353540"
                                    }
                                }
                            }
                        }
                    }
                    
                    // 添加分隔标签
                    Item {
                        Layout.fillWidth: true
                        height: 50
                        
                        Rectangle {
                            width: parent.width
                            height: 1
                            color: "#3E3E3E"
                            anchors.verticalCenter: parent.verticalCenter
                        }
                        
                        Label {
                            text: "关于"
                            color: "#CCCCCC"
                            font.pixelSize: 18
                            anchors.centerIn: parent
                            background: Rectangle {
                                anchors.fill: parent
                                anchors.margins: -10
                                color: "#1E1E2D"
                            }
                        }
                    }
                    
                    // 系统信息
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 150
                        color: "#262626"
                        radius: 10
                        
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 20
                            spacing: 10
                            
                            RowLayout {
                                spacing: 15
                                
                                Image {
                                    source: "assets/car_icon.png"
                                    sourceSize.width: 48
                                    sourceSize.height: 48
                                    fillMode: Image.PreserveAspectFit
                                }
                                
                                Label {
                                    text: "车载多模态交互系统"
                                    font.pixelSize: 20
                                    font.bold: true
                                    color: "white"
                                }
                            }
                            
                            Rectangle {
                                height: 1
                                Layout.fillWidth: true
                                color: "#3E3E3E"
                                Layout.topMargin: 5
                                Layout.bottomMargin: 5
                            }
                            
                            Label {
                                text: "版本: V1.0.0"
                                font.pixelSize: 16
                                color: "white"
                            }
                            
                            Label {
                                text: "© 2025 南开大学"
                                font.pixelSize: 14
                                color: "#AAAAAA"
                            }
                            
                            Item { Layout.fillHeight: true }
                            
                            Button {
                                text: "检查更新"
                                Layout.alignment: Qt.AlignRight
                                
                                contentItem: Text {
                                    text: parent.text
                                    color: "white"
                                    font.pixelSize: 14
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }
                                
                                background: Rectangle {
                                    implicitWidth: 120
                                    implicitHeight: 35
                                    color: parent.down ? "#0066CC" : "#0077DD"
                                    radius: 5
                                }
                            }
                        }
                    }
                    
                    Item { height: 20 } // 底部间距
                }
            }
        }
    }


    // —— 空调页面 —— //
    Component {
        id: acPage
        Page {
            background: Rectangle { color: "#1E1E2D" }

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 30
                spacing: 20

                // 页面标题
                Label {
                    text: "空调控制"
                    font.pixelSize: 28
                    font.bold: true
                    color: "white"
                    Layout.alignment: Qt.AlignHCenter
                    Layout.bottomMargin: 20
                }

                // 温度显示
                Rectangle {
                    Layout.alignment: Qt.AlignHCenter
                    width: 200
                    height: 200
                    radius: 100
                    color: "#262630"
                    border.width: 6
                    border.color: "#4CAF50"

                    Label {
                        anchors.centerIn: parent
                        text: "23°C"
                        font.pixelSize: 48
                        font.bold: true
                        color: "white"
                    }
                }

                // 温度控制
                RowLayout {
                    Layout.alignment: Qt.AlignHCenter
                    spacing: 40

                    Button {
                        width: 60
                        height: 60
                        
                        background: Rectangle {
                            radius: 30
                            color: parent.pressed ? "#454550" : "#353545" 
                            
                            Text {
                                anchors.centerIn: parent
                                text: "−"
                                color: "white"
                                font.pixelSize: 32
                            }
                        }
                    }

                    Button {
                        width: 60
                        height: 60
                        
                        background: Rectangle {
                            radius: 30
                            color: parent.pressed ? "#454550" : "#353545"
                            
                            Text {
                                anchors.centerIn: parent
                                text: "+"
                                color: "white"
                                font.pixelSize: 28
                            }
                        }
                    }
                }

                // 风速控制区域
                Rectangle {
                    Layout.fillWidth: true
                    height: 80
                    color: "#262630"
                    radius: 10
                    
                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 15
                        spacing: 20
                        
                        Label {
                            text: "风速"
                            font.pixelSize: 18
                            color: "white"
                            Layout.minimumWidth: 60
                        }
                        
                        Slider {
                            id: fanSpeedSlider
                            Layout.fillWidth: true
                            from: 1
                            to: 5
                            value: 3
                            stepSize: 1
                            
                            background: Rectangle {
                                x: fanSpeedSlider.leftPadding
                                y: fanSpeedSlider.topPadding + fanSpeedSlider.height / 2 - height / 2
                                width: fanSpeedSlider.availableWidth
                                height: 6
                                radius: 3
                                color: "#3E3E3E"
                                
                                Rectangle {
                                    width: fanSpeedSlider.visualPosition * parent.width
                                    height: parent.height
                                    color: "#2196F3"
                                    radius: 3
                                }
                            }
                            
                            handle: Rectangle {
                                x: fanSpeedSlider.leftPadding + fanSpeedSlider.visualPosition * fanSpeedSlider.availableWidth - width / 2
                                y: fanSpeedSlider.topPadding + fanSpeedSlider.height / 2 - height / 2
                                width: 20
                                height: 20
                                radius: 10
                                color: fanSpeedSlider.pressed ? "#f0f0f0" : "#f6f6f6"
                                border.color: "#bbb"
                            }
                        }
                        
                        Label {
                            text: Math.round(fanSpeedSlider.value) + " 档"
                            font.pixelSize: 18
                            color: "white"
                            Layout.minimumWidth: 45
                            horizontalAlignment: Text.AlignRight
                        }
                    }
                }

                // 模式选择区域
                Rectangle {
                    Layout.fillWidth: true
                    height: 80
                    color: "#262630"
                    radius: 10

                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 15
                        spacing: 15
                        
                        Label {
                            text: "模式"
                            font.pixelSize: 18
                            color: "white"
                        }
                        
                        Item { Layout.fillWidth: true }

                        // 自动模式
                        Rectangle {
                            width: 70
                            height: 50
                            radius: 8
                            color: "#4CAF50" // 选中状态
                            
                            Label {
                                anchors.centerIn: parent
                                text: "自动"
                                color: "white"
                                font.pixelSize: 14
                            }

                            MouseArea {
                                anchors.fill: parent
                                cursorShape: Qt.PointingHandCursor
                            }
                        }
                        
                        // 制冷模式
                        Rectangle {
                            width: 70
                            height: 50
                            radius: 8
                            color: "#353545"
                            
                            Label {
                                anchors.centerIn: parent
                                text: "制冷"
                                color: "white"
                                font.pixelSize: 14
                            }

                            MouseArea {
                                anchors.fill: parent
                                cursorShape: Qt.PointingHandCursor
                            }
                        }
                        
                        // 制热模式
                        Rectangle {
                            width: 70
                            height: 50
                            radius: 8
                            color: "#353545"
                            
                            Label {
                                anchors.centerIn: parent
                                text: "制热"
                                color: "white"
                                font.pixelSize: 14
                            }

                            MouseArea {
                                anchors.fill: parent
                                cursorShape: Qt.PointingHandCursor
                            }
                        }
                        
                        // 通风模式
                        Rectangle {
                            width: 70
                            height: 50
                            radius: 8
                            color: "#353545"
                            
                            Label {
                                anchors.centerIn: parent
                                text: "通风"
                                color: "white"
                                font.pixelSize: 14
                            }

                            MouseArea {
                                anchors.fill: parent
                                cursorShape: Qt.PointingHandCursor
                            }
                        }
                    }
                }

                Item { Layout.fillHeight: true }

                // 开关按钮
                Button {
                    Layout.alignment: Qt.AlignHCenter
                    Layout.bottomMargin: 20
                    width: 150
                    height: 60
                    
                    contentItem: Text {
                        text: "电源开关"
                        color: "white"
                        font.pixelSize: 18
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    
                    background: Rectangle {
                        radius: 10
                        color: parent.pressed ? "#CC3030" : "#E53935"
                    }
                }
            }
        }
    }

}
