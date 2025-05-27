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
    property string musicTitle: "暂无音乐播放"

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
                setMusicImage("assets/album_cover.png")
                musicTitle = "南开校歌"
                break
            case "TurnOnAC":
                setMusicImage("assets/album_cover.png")
                musicTitle = "南开校歌"
                break
            case "distract":
                setMusicImage("assets/album_cover.png")
                musicTitle = "南开校歌"
                break
            case "NoticeRoad":
                setMusicImage("assets/album_cover.png")
                musicTitle = "南开校歌"
                break
            }
        }
    }


    // 顶部导航栏
    Rectangle {
        id: headerRect
        width: parent.width
        height: 50
        color: "#2E2E2E"

        RowLayout {
            anchors.fill: parent
            anchors.margins: 10
            spacing: 20

            ToolButton {
                icon.name: "menu"
                onClicked: sidebar.visible = !sidebar.visible
                Layout.alignment: Qt.AlignVCenter
            }
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

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 10
            spacing: 10

            Button { text: "主页"; onClicked: stackView.replace(homePage) }
            Button { text: "音乐"; onClicked: stackView.replace(musicPage) }
        }
    }

    // 主内容区
    StackView {
        id: stackView
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
                    radius: 10
                    color: "#2E2E2E"
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    height: 150

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 10
                        Label { text: "21°C"; font.pixelSize: 24; color: "white" }
                        Label { text: "多云转晴"; color: "white" }
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
                                width: parent.width * 0.6
                                height: parent.height * 0.6
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
                    radius: 10
                    color: "#262626"
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    height: 150

                    ColumnLayout {
                        anchors.centerIn: parent
                        spacing: 10
                        Label { text: "空调"; font.pixelSize: 20; color: "white" }
                        Label { text: "23°C  自动"; color: "white" }
                    }
                }

                // 驾驶员状态卡片
                Rectangle {
                    radius: 10
                    color: "#262626"
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    height: 150

                    ColumnLayout {
                        anchors.centerIn: parent
                        spacing: 10
                        Label { text: "驾驶员状态"; font.pixelSize: 20; color: "white" }
                        ToolButton {
                            icon.name: "account-circle"
                            icon.width: 40
                            icon.height: 40
                        }
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

}
