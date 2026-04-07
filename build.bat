@echo off
chcp 65001 >nul
echo ======================================
echo  小学生朗读激励抽奖应用 - 打包脚本
echo  Phase 5: 自动化打包
echo ======================================
echo.

:: 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到Python，请先安装Python 3.10+
    pause
    exit /b 1
)

echo [步骤 1/5] 检查依赖包...
pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo [警告] PyInstaller未安装，正在安装...
    pip install pyinstaller
    if %errorlevel% neq 0 (
        echo [错误] PyInstaller安装失败
        pause
        exit /b 1
    )
)

echo [步骤 2/5] 清理旧的打包文件...
if exist "dist" (
    echo 正在清理dist目录...
    rmdir /s /q dist
)
if exist "build" (
    echo 正在清理build目录...
    rmdir /s /q build
)
echo 清理完成！

echo.
echo [步骤 3/5] 开始打包应用...
echo 使用配置文件: ReadActivator.spec
pyinstaller ReadActivator.spec --clean --noconfirm

if %errorlevel% neq 0 (
    echo.
    echo [错误] 打包失败！请检查错误信息。
    pause
    exit /b 1
)

echo.
echo [步骤 4/5] 检查打包结果...
if not exist "dist\ReadActivator\ReadActivator.exe" (
    echo [错误] 打包后的exe文件不存在
    pause
    exit /b 1
)

echo 打包成功！

echo.
echo [步骤 5/5] 复制必要文件到打包目录...

:: 确保data目录存在
if not exist "dist\ReadActivator\data" (
    mkdir "dist\ReadActivator\data"
)

:: 复制默认配置文件（如果存在）
if exist "data\config.json" (
    copy /y "data\config.json" "dist\ReadActivator\data\" >nul
    echo - 已复制配置文件
)

:: 复制图标文件
if exist "read.ico" (
    copy /y "read.ico" "dist\ReadActivator\" >nul
    echo - 已复制图标文件
)

:: 复制README（如果需要）
if exist "README.md" (
    copy /y "README.md" "dist\ReadActivator\" >nul
    echo - 已复制README文件
)

:: 创建使用说明文件
echo - 正在生成使用说明...
(
echo 小学生朗读激励抽奖应用 - 使用说明
echo ==========================================
echo.
echo 快速开始：
echo 1. 双击 ReadActivator.exe 启动程序
echo 2. 在配置页面选择麦克风设备
echo 3. 点击"开始测试"调整音量阈值
echo 4. 编辑奖项和权重（可选）
echo 5. 点击"开始活动"进入抽奖界面
echo 6. 学生大声朗读，结果将逐渐揭晓
echo.
echo 配置文件说明：
echo - 配置自动保存在 data\config.json
echo - 可以直接编辑该文件修改配置
echo.
echo 部署说明：
echo - 请将整个文件夹复制到目标电脑
echo - 不要只复制exe文件，需要包含_internal文件夹
echo.
echo 技术支持：
echo - 如遇问题，请检查麦克风权限设置
echo - Windows系统需要允许应用访问麦克风
echo.
echo 版本信息：
echo - 应用版本: 1.0.0
echo - 打包日期: %date% %time%
echo.
) > "dist\ReadActivator\使用说明.txt"

echo.
echo ======================================
echo  打包完成！
echo ======================================
echo.
echo 打包文件位置: dist\ReadActivator\
echo 可执行文件: dist\ReadActivator\ReadActivator.exe
echo.
echo 文件夹内容：
echo   ReadActivator\
echo   ├── ReadActivator.exe     (主程序)
echo   ├── _internal\            (依赖库，必须保留)
echo   ├── data\                 (配置目录)
echo   ├── 使用说明.txt
echo   └── README.md
echo.
echo 分发建议：
echo 1. 使用压缩工具将 dist\ReadActivator 整个文件夹打包成zip
echo 2. 分发时确保接收方解压后保持文件夹结构
echo 3. 提醒用户双击 ReadActivator.exe 启动
echo.

:: 询问是否启动应用
set /p launch=是否立即运行打包后的应用？(Y/N): 
if /i "%launch%"=="Y" (
    echo.
    echo 正在启动应用...
    start "" "dist\ReadActivator\ReadActivator.exe"
)

echo.
echo 打包脚本执行完毕！
pause
