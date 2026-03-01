CREATE Table lipstick(
    hex_code TEXT PRIMARY KEY,
    color_id TEXT,
    Foreign Key (color_id) REFERENCES color(color_id)
);
INSERT INTO lipstick (hex_code, color_id, name) VALUES ('#FFD1A3', '봄 웜톤', '애프리콧 베이지');
INSERT INTO lipstick (hex_code, color_id, name) VALUES ('#FFB997', '봄 웜톤', '누드 피치');
INSERT INTO lipstick (hex_code, color_id, name) VALUES ('#FF9966', '봄 웜톤', '쥬시 오렌지');
INSERT INTO lipstick (hex_code, color_id, name) VALUES ('#FF7F50', '봄 웜톤', '리빙 코랄');
INSERT INTO lipstick (hex_code, color_id, name) VALUES ('#F9A55E', '봄 웜톤', '선셋 진저');
INSERT INTO lipstick (hex_code, color_id, name) VALUES ('#FFC0CB', '봄 웜톤', '베이비 블라썸');
INSERT INTO lipstick (hex_code, color_id, name) VALUES ('#FFA07A', '봄 웜톤', '살몬 스무디');
INSERT INTO lipstick (hex_code, color_id, name) VALUES ('#FF8C69', '봄 웜톤', '루미너스 코랄');
INSERT INTO lipstick (hex_code, color_id, name) VALUES ('#A0522D', '가을 웜톤', '메이플 브라운');
INSERT INTO lipstick (hex_code, color_id, name) VALUES ('#8B4513', '가을 웜톤', '딥 에스프레소');
INSERT INTO lipstick (hex_code, color_id, name) VALUES ('#D2691E', '가을 웜톤', '시나몬 토스트');
INSERT INTO lipstick (hex_code, color_id, name) VALUES ('#C8A2C8', '여름 쿨톤', '라벤더 포그');
INSERT INTO lipstick (hex_code, color_id, name) VALUES ('#DDA0DD', '여름 쿨톤', '오키드 페탈');
INSERT INTO lipstick (hex_code, color_id, name) VALUES ('#BC8F8F', '여름 쿨톤', '더스티 로즈');
INSERT INTO lipstick (hex_code, color_id, name) VALUES ('#D8BFD8', '여름 쿨톤', '페일 아이리스');
INSERT INTO lipstick (hex_code, color_id, name) VALUES ('#C596B3', '여름 쿨톤', '모브 핑크');
INSERT INTO lipstick (hex_code, color_id, name) VALUES ('#E0B0FF', '여름 쿨톤', '밀키 라벤더');
INSERT INTO lipstick (hex_code, color_id, name) VALUES ('#B09C9D', '여름 쿨톤', '애쉬 로즈');
INSERT INTO lipstick (hex_code, color_id, name) VALUES ('#C0C0C0', '여름 쿨톤', '실버 글레이즈');
INSERT INTO lipstick (hex_code, color_id, name) VALUES ('#DC143C', '겨울 쿨톤', '루비 레드');
INSERT INTO lipstick (hex_code, color_id, name) VALUES ('#8B0000', '겨울 쿨톤', '뱀파이어 블러디');
INSERT INTO lipstick (hex_code, color_id, name) VALUES ('#4B0082', '겨울 쿨톤', '미드나잇 퍼플');
INSERT INTO lipstick (hex_code, color_id, name) VALUES ('#8A2BE2', '겨울 쿨톤', '일렉트릭 바이올렛');
INSERT INTO lipstick (hex_code, color_id, name) VALUES ('#FF00FF', '겨울 쿨톤', '네온 푸시아');
INSERT INTO lipstick (hex_code, color_id, name) VALUES ('#C71585', '겨울 쿨톤', '베리 크러시');
INSERT INTO lipstick (hex_code, color_id, name) VALUES ('#B22222', '겨울 쿨톤', '브릭 레드');
INSERT INTO lipstick (hex_code, color_id, name) VALUES ('#800080', '겨울 쿨톤', '로얄 퍼플');
INSERT INTO lipstick (hex_code, color_id, name) VALUES ('#B8860B', '가을 웜톤', '앤티크 골드');
INSERT INTO lipstick (hex_code, color_id, name) VALUES ('#CD5C5C', '가을 웜톤', '드라이 로즈');
INSERT INTO lipstick (hex_code, color_id, name) VALUES ('#B5651D', '가을 웜톤', '카라멜 라떼');
INSERT INTO lipstick (hex_code, color_id, name) VALUES ('#800000', '가을 웜톤', '마룬 레드');
INSERT INTO lipstick (hex_code, color_id, name) VALUES ('#A52A2A', '가을 웜톤', '코코아 브라운');