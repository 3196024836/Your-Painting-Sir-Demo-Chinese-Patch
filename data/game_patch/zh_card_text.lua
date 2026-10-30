-- Localize printed image text while preserving original game resources at runtime.
-- Original PNGs and gameplay image data remain unchanged.
local M = {}
local cards = {
    ["phone/quests/card_designer/rank1/cowering_squire"] = {
        title = "胆小侍从", lines = {"受攻击时返回", "拥有者手牌"},
        titleColor = {69, 87, 121}, effectColor = {66, 95, 75}
    },
    ["phone/quests/card_designer/rank1/jar_of_desire"] = {
        title = "欲望之壶", lines = {"抽2张牌"},
        titleColor = {118, 69, 121}, effectColor = {66, 78, 95}
    },
    ["phone/quests/card_designer/rank1/brubble"] = {
        title = "布拉布尔", lines = {"对手回合被消灭时，", "下回合开始时", "再得一颗红宝石。"},
        titleColor = {132, 29, 35}, effectColor = {56, 73, 105}
    }
}
local titleFont, effectFont
local function color(c)
    love.graphics.setColor(c[1] / 255, c[2] / 255, c[3] / 255, 1)
end

local firedFont
local function translateFired(image)
    assert(image:getWidth() == 362 and image:getHeight() == 38, "失败画面文字尺寸与补丁不匹配")
    if not firedFont then
        firedFont = love.graphics.newFont("assets/fonts/fusion-pixel-zh.ttf", 24)
        firedFont:setFilter("nearest", "nearest")
    end
    local title = "你被解雇了！"
    assert(firedFont:getWidth(title) <= 350 and firedFont:getHeight() <= 36, "失败画面文字超出尺寸")
    local canvas = love.graphics.newCanvas(362, 38, {dpiscale = 1})
    love.graphics.push("all")
    canvas:renderTo(function()
        love.graphics.clear(0, 0, 0, 0)
        love.graphics.setBlendMode("alpha", "alphamultiply")
        love.graphics.setFont(firedFont)
        -- Pixel-style red outline and pale inner letters, matching the source.
        love.graphics.setColor(0.68, 0.04, 0.03, 1)
        for dx = -1, 1 do for dy = -1, 1 do
            love.graphics.printf(title, dx, 1 + dy, 362, "center")
        end end
        love.graphics.setColor(1, 0.32, 0.23, 1)
        love.graphics.printf(title, 0, 1, 362, "center")
        love.graphics.setColor(1, 0.88, 0.75, 1)
        love.graphics.printf(title, 0, 0, 362, "center")
    end)
    love.graphics.pop()
    local output = love.graphics.newImage(canvas:newImageData())
    output:setFilter("nearest", "nearest")
    return output
end

-- The article pages have fixed positions in the version-locked atlas. Only verified
-- text-only rectangles are changed; illustrations and the original image data stay intact.
local newspaperFrames = {
    [0]={964,544}, [2]={964,1088}, [3]={482,1088}, [4]={0,1088}, [5]={1928,816},
    [6]={1446,816}, [7]={964,816}, [8]={482,816}, [9]={0,816},
    [10]={1928,544}, [11]={1446,544}, [12]={0,0}
}
-- Each rectangle has been checked against the original atlas: it contains text
-- and, where bg is specified, a single flat background colour only.
local newspaperRules = {
    {id="masthead-translation",page=0,box={300,5,110,15},lines={"早起鸟报"},size=10,color={78,75,74},align="center"},
    {id="masthead-slogan",page=0,box={298,69,115,14},lines={"新闻——印在纸上！"},size=10,color={78,75,74},bg={228,210,196,255},align="center"},
    {id="next",page=0,box={419,226,32,20},lines={"下一页"},size=10,dy=2,color={65,60,57},align="center"},
    -- Artwork lettering is retained where erasing it would destroy the picture;
    -- these captions occupy source-transparent margins of the same page.
    {id="mortar-caption",page=2,box={280,245,146,15},lines={"新品：研钵与研杵"},size=10,color={95,88,82},align="center"},
    {id="sunny-caption",page=3,box={30,8,175,17},lines={"阳光灿烂"},size=10,color={137,128,107},align="center"},
    {id="grape-water",page=3,box={170,98,59,26},lines={"葡萄水！"},size=12,dy=2,color={137,128,107}},
    {id="grape-deserve",page=3,box={18,122,95,27},lines={"你值得拥有……"},size=12,dy=2,color={193,188,176}},
    {id="grape-real",page=3,box={174,175,54,38},lines={"真正葡萄","口味"},size=12,step=16,color={92,88,79}},
    -- Keep the original grape label's frame and crossing line; replace only its interior.
    {id="grape-none",page=3,box={38,214,43,21},lines={"无真葡萄"},size=10,dy=4,color={191,180,171},align="center"},
    {id="icecream-title",page=3,box={273,42,156,21},lines={"尝尝新口味"},size=12,dy=2,color={79,75,70},bg={235,222,208,255},align="center",preserve={{384,42},{385,42}}},
    {id="icecream-mayo",page=3,box={310,76,80,14},lines={"蛋黄酱！"},size=10,color={189,176,159},bg={241,231,218,255},align="center"},
    {id="icecream-mud",page=3,box={270,121,29,15},lines={"泥巴。"},size=9,color={123,98,67},bg={241,231,218,255}},
    {id="icecream-gray",page=3,box={394,115,36,15},lines={"灰色……"},size=9,color={185,181,177},bg={241,231,218,255},preserve={{394,127},{395,128},{396,129},{394,128},{394,129},{395,129}}},
    {id="beach",page=4,box={39,31,119,63},lines={"去海滩玩吧！"},size=16,dy=16,color={255,255,255},outline={45,70,106},rowRef=170,align="center"},
    {id="cruise-title",page=5,box={254,25,197,24},lines={"游轮爆炸"},size=16,color={32,33,35},align="center"},
    {id="cruise-upper",page=5,box={315,55,91,36},lines={"“至少水是", "暖的！”", "——幸存者"},size=9,step=11,color={70,65,61},
        preserve={{395,82},{398,82},{399,82},{394,83},{395,83},{396,83},{397,83},{398,83},{400,83},{401,83}}},
    {id="cruise-middle",page=5,box={307,130,76,36},lines={"“水是暖的……","——幸存者"},size=9,dy=1,step=13,color={70,65,61}},
    {id="cruise-bottom",page=5,box={315,216,100,26},lines={"“是我。是我干的。”","——幸存者"},size=10,step=13,color={70,65,61}},
    {id="dancer-title",page=6,box={31,25,197,18},lines={"霹雳舞者重返小镇"},size=12,color={36,39,40}},
    {id="dancer-quote",page=6,box={31,212,198,13},lines={"把你所有的东西都藏好。——本地警长"},size=10,color={72,78,80}},
    {id="captain",page=6,box={255,134,85,55},lines={"招聘","船长"},size=16,dy=6,step=21,color={36,39,40},bg={215,196,185,255},align="center"},
    {id="salary",page=6,box={297,220,113,21},lines={"薪酬：$$$"},size=12,dy=2,color={36,39,40},align="center"},
    {id="monster-header",page=7,box={31,25,197,25},lines={"坐稳了！","疯狂怪兽电影时间到！！！"},size=10,step=12,color={22,20,20}},
    {id="monster-upper",page=7,box={93,62,125,37},lines={"“当然是外星人会赢。","他们有激光。”"},size=10,step=13,color={45,51,53}},
    {id="monster-middle",page=7,box={50,133,118,37},lines={"“船……宇宙飞船……","对海怪来说都一样！”"},size=10,step=13,color={45,51,53}},
    {id="monster-lower",page=7,box={91,188,137,49},lines={"其实……根据我的计算，","海盗获胜的机会最大！"},size=10,step=13,color={45,51,53}},
    {id="monster-poster-caption",page=7,box={255,242,195,14},lines={"外星人大战海怪：附近影院即将上映"},size=9,color={45,51,53},align="center"},
    {id="designer-caption",page=8,box={54,10,160,18},lines={"想成为游戏设计师？"},size=10,color={34,34,34},align="center"},
    {id="game-no-experience",page=8,box={54,118,160,14},lines={"无需经验（0）"},size=10,color={0,0,0},align="center"},
    {id="game-phone-label",page=8,box={83,98,34,14},lines={"电话："},size=10,color={0,0,0},bg={242,244,247,255}},
    {id="call-me-left",page=8,box={265,59,39,18},lines={"打给我"},size=10,dy=2,color={34,34,34}},
    {id="call-me-right",page=8,box={402,59,32,18},lines={},size=10,color={34,34,34}},
    {id="horse-title",page=9,box={31,26,197,18},lines={"马匹滑冰大获成功"},size=12,color={22,21,21}},
    {id="horse-quote",page=9,box={320,30,129,26},lines={"“我已经等不及看","马匹冰球了！”"},size=10,step=13,color={52,46,41}},
    {id="detective-title",page=9,box={251,109,199,16},lines={"破案招募助手"},size=12,color={34,34,34}},
    {id="detective-body",page=9,box={350,136,100,69},lines={"你好，谁能帮我","找到未解谜案中","缺失的拼图？"},size=12,step=16,color={34,34,34}},
    {id="detective-phone-label",page=9,box={359,218,31,14},lines={"电话："},size=10,color={34,34,34}},
    {id="cat-title",page=10,box={31,24,197,26},lines={"猫咪获救……又一次"},size=16,dy=2,color={57,61,62}},
    {id="cat-left",page=10,box={31,150,197,27},lines={"“毛球先生回来真是太好了！”","——理智的爱猫女士"},size=10,step=13,color={57,61,62}},
    {id="cat-right",page=10,box={376,78,79,41},lines={"每周都发生。","——消防员"},size=10,step=13,color={57,61,62}},
    {id="cat-bottom",page=10,box={254,194,132,15},lines={"“呕！！”——毛球先生"},size=10,color={57,61,62}},
    {id="pasta",page=11,box={39,26,126,29},lines={"美味……","意大利面"},size=10,step=13,color={154,136,123},lineColors={{198,179,166},{154,136,123}},rowRef=36},
    {id="pasta-with",page=11,box={176,60,37,14},lines={"配上……"},size=9,color={174,160,150},bg={238,226,217,255}},
    {id="pasta-meatballs",page=11,box={105,156,111,13},lines={"瑞典肉丸"},size=10,color={154,136,123},bg={238,226,217,255}},
    {id="cow-caption",page=11,box={254,250,201,15},lines={"新品：奶牛汁，马上就喝！"},size=10,color={86,79,76},align="center"},
    {id="thanks",page=12,box={31,52,129,22},lines={"感谢游玩"},size=16,color={69,69,69}},
    {id="thanks-line2",page=12,box={104,75,112,18},lines={},size=12,color={91,91,91}},
    {id="demo",page=12,box={172,163,56,18},lines={"试玩版！"},size=12,color={69,69,69}},
    {id="previous",page=12,box={25,225,60,19},lines={"上一页"},size=10,dy=2,color={65,60,57},align="center"},
}
M.newspaperRules = newspaperRules -- Shared with the isolated pixel-preservation test.

local function drawNewspaperRules()
    local fonts = {}
    local source = love.image.newImageData("assets/images/workshop/newspaper/content.png")
    for _, rule in ipairs(newspaperRules) do
        local frame = assert(newspaperFrames[rule.page])
        local b = rule.box
        local x, y, w, h = frame[1]+b[1], frame[2]+b[2], b[3], b[4]
        local font = fonts[rule.size]
        if not font then
            font = love.graphics.newFont("assets/fonts/fusion-pixel-zh.ttf", rule.size)
            font:setFilter("nearest", "nearest"); fonts[rule.size] = font
        end
        local dy, step = rule.dy or 0, rule.step or font:getHeight()
        if #rule.lines > 0 then
            assert(dy+(#rule.lines-1)*step+font:getHeight() <= h, "报纸文字高度超出范围："..rule.id)
            for _, line in ipairs(rule.lines) do
                assert(font:getWidth(line) <= w, "报纸文字宽度超出范围："..rule.id)
            end
        end
        love.graphics.setBlendMode("replace", "premultiplied")
        if rule.rowRef then
            for row=0,h-1 do
                love.graphics.setColor(source:getPixel(frame[1]+rule.rowRef,y+row))
                love.graphics.rectangle("fill",x,y+row,w,1)
            end
        else
            local bg=rule.bg or {0,0,0,0}
            love.graphics.setColor(bg[1]/255,bg[2]/255,bg[3]/255,bg[4]/255)
            love.graphics.rectangle("fill",x,y,w,h)
        end
        love.graphics.setBlendMode("alpha", "alphamultiply");love.graphics.setFont(font)
        for i,line in ipairs(rule.lines) do
            local yy=y+dy+(i-1)*step
            if rule.outline then
                local c=rule.outline;love.graphics.setColor(c[1]/255,c[2]/255,c[3]/255,1)
                for ox=-1,1 do for oy=-1,1 do love.graphics.printf(line,x+ox,yy+oy,w,"center") end end
            end
            local c=(rule.lineColors and rule.lineColors[i]) or rule.color
            love.graphics.setColor(c[1]/255,c[2]/255,c[3]/255,1)
            if rule.align == "center" then love.graphics.printf(line,x,yy,w,"center")
            else love.graphics.print(line,x,yy) end
        end
        if rule.preserve then
            love.graphics.setBlendMode("replace", "premultiplied")
            for _,p in ipairs(rule.preserve) do
                love.graphics.setColor(source:getPixel(frame[1]+p[1],frame[2]+p[2]))
                love.graphics.rectangle("fill",frame[1]+p[1],frame[2]+p[2],1,1)
            end
        end
    end
end

local function translateNewspaper(image)
    assert(image:getWidth() == 2410 and image:getHeight() == 1360, "报纸图集尺寸与补丁不匹配")
    local headlineFont = love.graphics.newFont("assets/fonts/fusion-pixel-zh.ttf", 12)
    local quoteFont = love.graphics.newFont("assets/fonts/fusion-pixel-zh.ttf", 12)
    headlineFont:setFilter("nearest", "nearest")
    quoteFont:setFilter("nearest", "nearest")
    local headline = "数千只闹钟被召回"
    local quote = {"“我很同情那些", "靠它早起的人。”", "——制造商"}
    assert(headlineFont:getWidth(headline) <= 190 and headlineFont:getHeight() <= 16, "报纸标题过长")
    for _, line in ipairs(quote) do
        assert(quoteFont:getWidth(line) <= 153, "报纸引文过长")
    end
    assert(quoteFont:getHeight() + 24 <= 40, "报纸引文字体过高")
    local appleTitle = "苹果应该被禁止吗？"
    local leftQuote = {"它们太可怕了。", "——本地医生"}
    local rightQuote = {"“其实我很喜欢", "苹果！”", "——教师"}
    local appleFont = love.graphics.newFont("assets/fonts/fusion-pixel-zh.ttf", 16)
    local smallFont = love.graphics.newFont("assets/fonts/fusion-pixel-zh.ttf", 10)
    appleFont:setFilter("nearest", "nearest"); smallFont:setFilter("nearest", "nearest")
    assert(appleFont:getWidth(appleTitle) <= 190 and appleFont:getHeight() <= 44, "苹果文章标题过长")
    for _, line in ipairs(leftQuote) do assert(smallFont:getWidth(line) <= 83, "苹果文章左引语过长") end
    for _, line in ipairs(rightQuote) do assert(smallFont:getWidth(line) <= 72, "苹果文章右引语过长") end
    assert(smallFont:getHeight() + 24 <= 40, "苹果文章引文字体过高")
    local ox, oy = 964, 544
    local canvas = love.graphics.newCanvas(2410, 1360, {dpiscale = 1})
    love.graphics.push("all")
    canvas:renderTo(function()
        love.graphics.clear(0, 0, 0, 0)
        love.graphics.setBlendMode("replace", "premultiplied")
        love.graphics.setColor(1, 1, 1, 1)
        love.graphics.draw(image, 0, 0)
        -- Clear text-only rectangles to transparency, leaving the paper and illustration unchanged.
        love.graphics.setColor(0, 0, 0, 0)
        love.graphics.rectangle("fill", ox + 258, oy + 96, 192, 16)
        love.graphics.rectangle("fill", ox + 258, oy + 194, 154, 40)
        love.graphics.setBlendMode("alpha", "alphamultiply")
        love.graphics.setColor(22/255, 22/255, 22/255, 1)
        love.graphics.setFont(headlineFont)
        love.graphics.print(headline, ox + 258, oy + 96)
        love.graphics.setColor(69/255, 68/255, 68/255, 1)
        love.graphics.setFont(quoteFont)
        for i, line in ipairs(quote) do
            love.graphics.print(line, ox + 258, oy + 194 + (i-1)*12)
        end
        local px, py = 1446, 1088
        love.graphics.setBlendMode("replace", "premultiplied"); love.graphics.setColor(0, 0, 0, 0)
        love.graphics.rectangle("fill", px + 30, py + 26, 190, 44)
        love.graphics.rectangle("fill", px + 73, py + 70, 13, 4)
        love.graphics.rectangle("fill", px + 134, py + 106, 83, 35)
        love.graphics.rectangle("fill", px + 288, py + 27, 72, 40)
        love.graphics.setBlendMode("alpha", "alphamultiply")
        love.graphics.setColor(92/255, 92/255, 92/255, 219/255); love.graphics.setFont(appleFont)
        love.graphics.printf(appleTitle, px + 30, py + 31, 190, "center")
        love.graphics.setColor(62/255, 52/255, 48/255, 1); love.graphics.setFont(smallFont)
        for i, line in ipairs(leftQuote) do love.graphics.print(line, px + 134, py + 106 + (i-1)*13) end
        for i, line in ipairs(rightQuote) do love.graphics.print(line, px + 288, py + 27 + (i-1)*12) end
        local fx, fy = 964, 1088
        local fishTitle = "本地渔夫捕获会说话的鱼"
        local fishTop = {"“希望它能", "闭嘴。”", "——渔夫"}
        local fishBottom = "“这条鱼话可真多！”——渔夫"
        local pestle = "（研杵另售$20.-）"
        assert(appleFont:getWidth(fishTitle) <= 197, "渔夫文章标题过长")
        for _, line in ipairs(fishTop) do assert(smallFont:getWidth(line) <= 72, "渔夫文章引语过长") end
        assert(headlineFont:getWidth(fishBottom) <= 197 and headlineFont:getHeight() <= 20, "渔夫文章下引语过长")
        assert(smallFont:getWidth(pestle) <= 146 and smallFont:getHeight() <= 16, "研杵广告过长")
        love.graphics.setBlendMode("replace", "premultiplied"); love.graphics.setColor(0, 0, 0, 0)
        love.graphics.rectangle("fill", fx + 31, fy + 25, 197, 41)
        love.graphics.rectangle("fill", fx + 310, fy + 32, 72, 40)
        love.graphics.rectangle("fill", fx + 31, fy + 219, 197, 20)
        love.graphics.rectangle("fill", fx + 280, fy + 229, 146, 16)
        love.graphics.setBlendMode("alpha", "alphamultiply")
        love.graphics.setColor(70/255, 65/255, 61/255, 1); love.graphics.setFont(appleFont)
        love.graphics.printf(fishTitle, fx + 31, fy + 29, 197, "center")
        love.graphics.setColor(92/255, 91/255, 89/255, 1); love.graphics.setFont(smallFont)
        for i, line in ipairs(fishTop) do love.graphics.print(line, fx + 310, fy + 32 + (i-1)*12) end
        love.graphics.setColor(70/255, 65/255, 61/255, 1); love.graphics.setFont(headlineFont)
        love.graphics.print(fishBottom, fx + 31, fy + 220)
        love.graphics.setColor(151/255, 150/255, 148/255, 1); love.graphics.setFont(smallFont)
        love.graphics.printf(pestle, fx + 280, fy + 229, 146, "center")
        drawNewspaperRules()
    end)
    love.graphics.pop()
    local output = love.graphics.newImage(canvas:newImageData())
    output:setFilter("nearest", "nearest")
    return output
end

-- UI art contains printed English rather than live text. Rebuild only the
-- original glyph pixels; preserve alpha, frames, button art and hit boxes.
local ui = {
    ["screens/menu/options/play"] = {
        size={306,78}, regions={
            {box={20,10,120,19}, colors={{255,255,255}}, text="开始新游戏", x=0,y=9,w=153,size=12},
            {box={173,10,120,19}, colors={{255,255,255}}, text="继续游戏", x=153,y=9,w=153,size=12},
            {box={20,49,120,19}, colors={{255,255,255}}, text="沙盒模式", x=0,y=48,w=153,size=12},
        }, textColor={255,255,255}},
    ["workshop/canvas/button_snap"] = {
        size={126,58}, regions={
            {box={8,7,48,15}, colors={{242,242,242},{255,255,255}}, text="拍照", x=0,y=8,w=63,size=12},
            {box={71,7,48,15}, colors={{242,242,242},{255,255,255}}, text="拍照", x=63,y=8,w=63,size=12},
            {box={8,36,48,15}, colors={{242,242,242},{255,255,255}}, text="拍照", x=0,y=37,w=63,size=12},
        }, textColor={242,242,242}},
    ["phone/screens/profile/history_button"] = {
        size={66,31}, regions={
            {box={10,8,49,14}, colors={{255,255,255}}, text="记录", x=0,y=8,w=66,size=12},
        }, textColor={255,255,255}},
    ["phone/screens/quest/picture_button"] = {
        size={66,31}, regions={
            {box={24,8,39,14}, colors={{255,255,255}}, text="图片", x=23,y=8,w=40,size=12},
        }, textColor={255,255,255}},
    ["paintings/1/pamphlet"] = {
        size={940,266}, regions={
            {box={20,5,200,74}, colors={{255,255,255}}, text="绝对真迹",x=20,y=15,w=200,size=12,scale=2},
        }, extra={{text="艺术拍卖行",x=20,y=43,w=200,size=12,scale=2}}, textColor={255,255,255}},
    ["paintings/2/pamphlet"] = {
        size={940,266}, regions={
            {box={20,5,200,74}, colors={{255,255,255}}, text="保证真迹",x=20,y=15,w=200,size=12,scale=2},
        }, extra={{text="艺术拍卖行",x=20,y=43,w=200,size=12,scale=2}}, textColor={255,255,255}},
    ["workshop/notes/button_steam"] = {
        size={111,51}, regions={
            {box={8,4,95,19}, colors={{55,52,53}}, text="加入愿望单",x=0,y=5,w=111,size=12},
        }, textColor={55,52,53}},
    ["workshop/notes/newspaper_end"] = {
        size={224,206}, regions={
            {box={59,8,98,16}, colors={{30,39,108}}, text="别忘了",x=40,y=9,w=132,size=10},
            {box={8,105,90,36}, colors={{30,39,108},{255,255,255}}, text="关注动态、",x=8,y=105,w=92,size=10},
            {box={126,112,90,28}, colors={{30,39,108},{255,255,255}}, text="关注 @Voskip",x=123,y=112,w=95,size=10},
        }, extra={{text="反馈与交流：",x=8,y=118,w=92,size=10}}, textColor={30,39,108}},
}
local gold = {
    ["workshop/canvas/button_done"] = {size={256,90},frame={64,30},colors={{233,211,167},{242,229,201}},x0=10,x1=53,text="完成"},
    ["screens/gallery/continue"] = {size={384,87},frame={96,29},colors={{255,248,226}},x0=9,x1=86,text="继续"},
}
local uiFonts = {}
local function sameColor(data, x, y, colors)
    local r,g,b,a = data:getPixel(x,y)
    if a < 0.99 then return false end
    for _, c in ipairs(colors) do
        if math.abs(r*255-c[1])<0.5 and math.abs(g*255-c[2])<0.5 and math.abs(b*255-c[3])<0.5 then return true end
    end
    return false
end

-- Remove the old lettering by interpolating its nearest background pixels on
-- the same row. Animated shine and the surrounding texture remain in place.
local function eraseGlyphs(data, source, box, mask)
    local x0,y0,w,h=unpack(box)
    for y=y0,y0+h-1 do for x=x0,x0+w-1 do
        if mask(x,y) then
            local l=x-1; while l>=x0 and mask(l,y) do l=l-1 end
            local r=x+1; while r<x0+w and mask(r,y) do r=r+1 end
            if l<x0 then l=r end
            if r>=x0+w then r=l end
            assert(l>=x0 and r<x0+w, "图片文字遮盖整行，不能安全擦除")
            local lr,lg,lb,la=source:getPixel(l,y)
            local rr,rg,rb,ra=source:getPixel(r,y)
            local t=(l==r) and 0 or (x-l)/(r-l)
            data:setPixel(x,y,lr+(rr-lr)*t,lg+(rg-lg)*t,lb+(rb-lb)*t,la+(ra-la)*t)
        end
    end end
end
local function uiFont(size)
    if not uiFonts[size] then
        uiFonts[size]=love.graphics.newFont("assets/fonts/fusion-pixel-zh.ttf",size)
        uiFonts[size]:setFilter("nearest","nearest")
    end
    return uiFonts[size]
end
local function drawUiText(spec, textColor)
    local font=uiFont(spec.size)
    local scale=spec.scale or 1
    assert(font:getWidth(spec.text)*scale<=spec.w, "界面图片中文超出边界")
    love.graphics.setFont(font)
    color(spec.color or textColor)
    love.graphics.push()
    love.graphics.translate(spec.x,spec.y)
    love.graphics.scale(scale,scale)
    love.graphics.printf(spec.text,0,0,spec.w/scale,spec.align or "center")
    love.graphics.pop()
end
local function translateUI(path, image, spec, goldSpec)
    local width,height=image:getWidth(),image:getHeight()
    local expected=(spec or goldSpec).size
    assert(width==expected[1] and height==expected[2], "界面图片尺寸与补丁不匹配")
    local filename="assets/images/"..path..".png"
    local source=love.image.newImageData(filename)
    local result=love.image.newImageData(filename)
    local draws={}
    local textColor
    if spec then
        textColor=spec.textColor
        for _,region in ipairs(spec.regions) do
            local box=region.box
            eraseGlyphs(result,source,box,function(x,y) return sameColor(source,x,y,region.colors) end)
            table.insert(draws,region)
        end
        for _,extra in ipairs(spec.extra or {}) do table.insert(draws,extra) end
    else
        textColor={255,248,226}
        local fw,fh=unpack(goldSpec.frame)
        for frame=0,10 do
            local fx=(frame%4)*fw; local fy=math.floor(frame/4)*fh
            -- The final (pressed) frame shifts its lettering down by one pixel.
            local pressOffset = frame==10 and 1 or 0
            local box={fx+goldSpec.x0,fy+9+pressOffset,goldSpec.x1-goldSpec.x0+1,9}
            eraseGlyphs(result,source,box,function(x,y)
                return sameColor(source,x-fx,y-fy-pressOffset,goldSpec.colors)
            end)
            table.insert(draws,{text=goldSpec.text,x=fx,y=fy+6+pressOffset,w=fw,size=12})
        end
    end
    local canvas=love.graphics.newCanvas(width,height,{dpiscale=1})
    love.graphics.push("all")
    canvas:renderTo(function()
        love.graphics.clear(0,0,0,0); love.graphics.setBlendMode("replace","premultiplied")
        love.graphics.setColor(1,1,1,1); love.graphics.draw(love.graphics.newImage(result),0,0)
        love.graphics.setBlendMode("alpha","alphamultiply")
        for _,draw in ipairs(draws) do drawUiText(draw,textColor) end
    end)
    love.graphics.pop()
    local output=love.graphics.newImage(canvas:newImageData()); output:setFilter("nearest","nearest")
    return output
end

function M.translate(path, image)
    if ui[path] or gold[path] then return translateUI(path, image, ui[path], gold[path]) end
    if path == "workshop/newspaper/content" then return translateNewspaper(image) end
    if path == "cutscenes/evaluations/hector/fired/text" then return translateFired(image) end
    local card = cards[path]
    if not card then return image end
    assert(image:getWidth() == 134 and image:getHeight() == 238, "卡牌图片尺寸与补丁不匹配")
    if not titleFont then
        titleFont = love.graphics.newFont("assets/fonts/fusion-pixel-zh.ttf", 12)
        effectFont = love.graphics.newFont("assets/fonts/fusion-pixel-zh.ttf", 12)
        titleFont:setFilter("nearest", "nearest")
        effectFont:setFilter("nearest", "nearest")
    end
    assert(titleFont:getWidth(card.title) <= 118, "卡牌标题过长")
    for _, line in ipairs(card.lines) do
        assert(effectFont:getWidth(line) <= 112, "卡牌说明过长")
    end
    assert((#card.lines - 1) * 12 + effectFont:getHeight() <= 40, "卡牌说明行数过多")
    local canvas = love.graphics.newCanvas(134, 238, {dpiscale = 1})
    love.graphics.push("all")
    canvas:renderTo(function()
        love.graphics.clear(0, 0, 0, 0)
        love.graphics.setBlendMode("replace", "premultiplied")
        love.graphics.setColor(1, 1, 1, 1)
        love.graphics.draw(image, 0, 0)
        color(card.titleColor); love.graphics.rectangle("fill", 5, 15, 125, 14)
        color(card.effectColor); love.graphics.rectangle("fill", 9, 173, 116, 40)
        love.graphics.setBlendMode("alpha", "alphamultiply")
        love.graphics.setFont(titleFont)
        love.graphics.setScissor(5, 15, 125, 14)
        love.graphics.setColor(0, 0, 0, 0.8)
        love.graphics.printf(card.title, 6, 15, 123, "center")
        love.graphics.setColor(1, 1, 1, 1)
        love.graphics.printf(card.title, 5, 14, 123, "center")
        love.graphics.setFont(effectFont)
        love.graphics.setScissor(9, 173, 116, 40)
        for i, line in ipairs(card.lines) do
            local y = 173 + (i - 1) * 12
            love.graphics.setColor(0, 0, 0, 0.65); love.graphics.print(line, 12, y + 1)
            love.graphics.setColor(1, 1, 1, 1); love.graphics.print(line, 11, y)
        end
        love.graphics.setScissor()
    end)
    love.graphics.pop()
    local output = love.graphics.newImage(canvas:newImageData())
    output:setFilter("nearest", "nearest")
    return output
end
return M

