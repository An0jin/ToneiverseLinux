-- 퍼스널 컬러 테이블 제작
CREATE table color(
    color_id  TEXT PRIMARY KEY,-- 퍼스널 컬러
    description TEXT-- 설명
);

INSERT INTO color (color_id, description) VALUES
('가을 웜톤', '가을 웜톤은 깊고 풍부하며 지구의 톤을 가진 톤입니다.'),
('봄 웜톤', '봄 웜톤은 밝고 신선하며 빛의 톤을 가진 톤입니다.'),
('여름 쿨톤', '여름 쿨톤은 부드럽고 희석하며 파란색의 톤을 가진 톤입니다.'),
('겨울 쿨톤', '겨울 쿨톤은 강하고 대비가 높고 얼음의 톤을 가진 톤입니다.');
