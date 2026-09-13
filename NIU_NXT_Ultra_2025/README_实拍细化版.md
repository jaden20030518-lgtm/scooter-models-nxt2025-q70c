# NIU NXT Ultra 2025 · 实拍细化版

本轮独立重生成模型，未覆盖 `Production_NIU`。主文件为 `NIU_NXT_2025_Refined.blend`；可编辑生成源码为 `build_niu_refined.py`、`production_details.py`、`refine_assemblies.py`。场景保留米制、+X 向前、+Y 向左。

保留官方黑色短单人座＋后伸镂空货架配置。大座试驾片仅用于共享零件细节，不把大座、短扶手和贴座尾灯移植到基准模型。双圆镜独立安装，参考同款行驶实拍；门店短座车未装镜被视为交车装配状态。

本轮画面来源：[2025 款拆解视频](https://www.douyin.com/video/7543589660329561359)、[Ultra 2025 试驾视频](https://www.douyin.com/video/7528096986893913379)、[黑色门店实车视频](https://www.douyin.com/video/7575140258804749903)。视频均按关键帧检查，未把此工作表述为全片连续观看。短座货架的主轮廓继续采用原任务保存的官方参考图。

## 实际网格变化

- 前灯从单中心投射筒改为三块横排浅扁光学窗口和共用水平框；圆灯盖、白色扩散环、带凸肋的载板、烟色透明外罩分为独立物体。主要依据拆解视频 520/526 秒，以及试驾 24/34.5 秒。灯盖采用有厚度的平法线前表面，避免平滑法线造成异常放大。
- 前围保留原始侧轮廓标定，横截面收紧内侧回折，减少均匀鼓胀；新增外罩密封边界和独立内衬、实际储物口及内部壁面。下检修盖按当前内衬逐点贴合，点火圆件与挂钩也随实际表面定位。
- 短座保持原厂长度，收窄前端并薄化前下沿；新增有真实开口的独立座桶、双口沿、刚性座底、前铰链与锁扣。开座预览通过旋转实际座垫和座底生成。
- 前后刹车重建为窄摩擦环、真正内开窗、连接臂和独立开槽 ABS 环；后轮改为满盘电机盖、分区金属装饰与周向固定点。轮中心与已有轮距标定保持不变。
- 驾驶舱重建为围绕横置 TFT 的折面壳、银色屏框和下缘桥；新增双圆镜。下侧裙增加顺接的薄壳过渡，踏板纹逐点贴在封厚后的内衬表面。

## 预览与复现

所有预览为同一灯光、曝光和相机设置下的真实 Blender 渲染，1200×900、Cycles 24 samples、最多 3 个 CPU 线程；本机可用 Metal 加速。没有生成式修图。

- `NIU_refined_hero_1200.png` / `NIU_refined_optics_1200.png` / `NIU_refined_side_1200.png`：新模型的前 3/4、前灯近景与侧面。
- `NIU_baseline_hero_1200.png` / `NIU_baseline_optics_1200.png` / `NIU_baseline_side_1200.png`：旧模型按完全相同设置重渲。
- `NIU_comparison_hero.png` / `NIU_comparison_optics.png` / `NIU_comparison_side.png`：左右并列比较。
- `NIU_refined_cockpit_1200.png` / `NIU_refined_bucket_1200.png`：内围和实际开座检查图。

生成：`Blender --background --threads 3 --python build_niu_refined.py`。

预览：`Blender --background --threads 3 --python render_previews.py`；旧版对照追加 `-- --baseline`。旧版对照读取同级 `Production_NIU` 文件夹，该历史工程不在仓库中，需要另行提供。已经渲染的旧版对照 PNG 随仓库保存；主模型的重生成不依赖旧 `.blend`。

检查：`Blender --background --threads 3 --python verify_refined.py`。结果写入 `NIU_refined_validation.json`，包含由轴心物体实测的轮距、踏步空间六条射线、三主光学区、旧单透镜残留、临时布尔刀具与非有限坐标检查。

冻结版 V6 已通过以上检查：448 个车体物体，轴心物体测得轮距 1.244562268 m。曾出现透底的前围右上像素 `(1014,299)` 现首命中连续内侧回边，封口射线检查通过。侧面、前灯、驾驶舱及开座图已做视觉检查。

## 仍属视觉近似的部分

轮距沿用原始图像标定约 1.24456 m，不将视频字幕 1255/760 mm 冒充官方尺寸。壳体横截面、灯组深度、屏框厚度、储物口/座桶/铰链尺寸和制动盘孔数仍为公开图像的视觉重建，未获得厂家 CAD 或工程测量。前壳肩部曲率、座垫表皮截面、尾挡泥板与摇臂罩仍可继续通过更多等视角素材提高准确度；本文件不是制造图或完整工程装配验证。

4K 主图及 2400px 细节图已保存在 `展示图/`，GLB 已导出并重新导入校核；结果见 `independent_validation.json`。
