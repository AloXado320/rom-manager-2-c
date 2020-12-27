import struct
import GeoWrite as GW
import F3D
import ColParse
import sys
import os
from pathlib import Path
from capstone import *
import shutil
from bitstring import *

#skip ending for now because script inf loops or something idk
#needs investigation
Num2Name = {
    4:'bbh',
    5:"ccm",
    6:'castle_inside',
    7:'hmc',
    8:'ssl',
    9:'bob',
    10:'sl',
    11:'wdw',
    12:'jrb',
    13:'thi',
    14:'ttc',
    15:'rr',
    16:"castle_grounds",
    17:'bitdw',
    18:'vcutm',
    19:'bitfs',
    20:'sa',
    21:'bits',
    22:'lll',
    23:'ddd',
    24:'wf',
    # 25:'ending',
    26:'castle_courtyard',
    27:'pss',
    28:'cotmc',
    29:'totwc',
    30:'bowser_1',
    31:'wmotr',
    33:'bowser_2',
    34:'bowser_3',
    36:'ttm'
}

#level specific banks have different addresses than vanilla, so I need a dict for them.

#all skyboxes are in bank 0xA
#in cmd, it goes:
#LOAD_MIO0(0xA,str+SegmentRomStart,str+SegmentRomEnd)
skyboxes = {
	0xB35770:'_water_skybox_mio0',
	0xB5D8B0:'_ccm_skybox_mio0',
	0xBEADB0:'_clouds_skybox_mio0',
	0xBA2330:'_bitfs_skybox_mio0',
	0xBC2C70:'_wdw_skybox_mio0',
	0xB859F0:'_cloud_floor_skybox_mio0',
	0xC12EF0:'_ssl_skybox_mio0',
	0xC3B030:'_bbh_skybox_mio0',
	0xC57970:'_bidw_skybox_mio0',
	0xC7FAB0:'_bits_skybox_mio0'
}

#name of actor group, bank gfx is in, bank geo is in
#for gfx it goes:
#LOAD_MIO0(bank,'_'+str+'_mio0SegmentRomStart',same w/ end)
#for geo it goes:
#LOAD_RAW(bank,'_'+str+'_geoSegmentRomStart',same w/ end)
#I will identify which are used by geo bank starts
#the last member is the global scripts to include after loading
#the bank
actors = {
	0x132850:['_group1', 5, 12,'script_func_global_2'],
	0x134a70:['_group2', 5, 12,'script_func_global_3'],
	0x13B5D0:['_group3', 5, 12,'script_func_global_4'],
	0x145C10:['_group4', 5, 12,'script_func_global_5'],
	0x151B70:['_group5', 5, 12,'script_func_global_6'],
	0x1602E0:['_group6', 5, 12,'script_func_global_7'],
	0x1656E0:['_group7', 5, 12,'script_func_global_8'],
	0x166BD0:['_group8', 5, 12,'script_func_global_9'],
	0x16D5C0:['_group9', 5, 12,'script_func_global_10'],
	0x180540:['_group10', 5, 12,'script_func_global_11'],
	0x187FA0:['_group11', 5, 12,'script_func_global_12'],
	0x1B9070:['_group12', 6, 13,'script_func_global_13'],
	0x1C3DB0:['_group13', 6, 13,'script_func_global_14'],
	0x1D7C90:['_group14', 6, 13,'script_func_global_15'],
	0x1E4BF0:['_group15', 6, 13,'script_func_global_16'],
	0x1E7D90:['_group16', 6, 13,'script_func_global_17'],
	0x1F1B30:['_group17', 6, 13,'script_func_global_18'],
	0x2008D0:['_common0', 8, 15,'script_func_global_1']
}

#addresses of banks for each specific level, just using RM start addr
LevelSpecificBanks = {
    0x00DB1610:'bbh',
    0x00DE0460:"ccm",
    0x00E0BC10:'castle_inside',
    0x00E8CD30:'hmc',
    0x00EC06A0:'ssl',
    0x00EF0F50:'bob',
    0x00F0A720:'sl',
    0x00F221B0:'wdw',
    0x00F42940:'jrb',
    0x00F5BCF0:'thi',
    0x00F720B0:'ttc',
    0x00F90AD0:'rr',
    0x00FC7950:"castle_grounds",
    0x00FE11D0:'bitdw',
    0x00FF9000:'vcutm',
    0x0100BCD0:'bitfs',
    0x01034C10:'bits',
    0x01058410:'lll',
    0x01088CE0:'ddd',
    0x010A09F0:'wf',
    0x010E9B60:'castle_courtyard',
    0x01125A30:'pss',
    0x0115C680:'bowser_2',
    0x01166220:'bowser_3',
    0x011732E0:'ttm'
}
#models to load for each level specific bank
LevelSpecificModels = {
    "ccm":"""LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_03, ccm_geo_00042C),
LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_04, ccm_geo_00045C),
LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_05, ccm_geo_000494),
LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_06, ccm_geo_0004BC),
LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_07, ccm_geo_0004E4),
LOAD_MODEL_FROM_GEO(MODEL_CCM_CABIN_DOOR,    cabin_door_geo),
LOAD_MODEL_FROM_GEO(MODEL_CCM_SNOW_TREE,     snow_tree_geo),
LOAD_MODEL_FROM_GEO(MODEL_CCM_ROPEWAY_LIFT,  ccm_geo_0003D0),
LOAD_MODEL_FROM_GEO(MODEL_CCM_SNOWMAN_BASE,  ccm_geo_0003F0),
LOAD_MODEL_FROM_GEO(MODEL_CCM_SNOWMAN_HEAD,  ccm_geo_00040C),
""",
	'bbh':"""LOAD_MODEL_FROM_GEO(MODEL_BBH_HAUNTED_DOOR,           haunted_door_geo),
LOAD_MODEL_FROM_GEO(MODEL_BBH_STAIRCASE_STEP,         geo_bbh_0005B0),
LOAD_MODEL_FROM_GEO(MODEL_BBH_TILTING_FLOOR_PLATFORM, geo_bbh_0005C8),
LOAD_MODEL_FROM_GEO(MODEL_BBH_TUMBLING_PLATFORM,      geo_bbh_0005E0),
LOAD_MODEL_FROM_GEO(MODEL_BBH_TUMBLING_PLATFORM_PART, geo_bbh_0005F8),
LOAD_MODEL_FROM_GEO(MODEL_BBH_MOVING_BOOKSHELF,       geo_bbh_000610),
LOAD_MODEL_FROM_GEO(MODEL_BBH_MESH_ELEVATOR,          geo_bbh_000628),
LOAD_MODEL_FROM_GEO(MODEL_BBH_MERRY_GO_ROUND,         geo_bbh_000640),
LOAD_MODEL_FROM_GEO(MODEL_BBH_WOODEN_TOMB,            geo_bbh_000658),
""",
    'castle_inside':"""LOAD_MODEL_FROM_GEO(MODEL_CASTLE_BOWSER_TRAP,        castle_geo_000F18),
LOAD_MODEL_FROM_GEO(MODEL_CASTLE_WATER_LEVEL_PILLAR, castle_geo_001940),
LOAD_MODEL_FROM_GEO(MODEL_CASTLE_CLOCK_MINUTE_HAND,  castle_geo_001530),
LOAD_MODEL_FROM_GEO(MODEL_CASTLE_CLOCK_HOUR_HAND,    castle_geo_001548),
LOAD_MODEL_FROM_GEO(MODEL_CASTLE_CLOCK_PENDULUM,     castle_geo_001518),
LOAD_MODEL_FROM_GEO(MODEL_CASTLE_CASTLE_DOOR,        castle_door_geo),
LOAD_MODEL_FROM_GEO(MODEL_CASTLE_WOODEN_DOOR,        wooden_door_geo),
LOAD_MODEL_FROM_GEO(MODEL_CASTLE_METAL_DOOR,         metal_door_geo),
LOAD_MODEL_FROM_GEO(MODEL_CASTLE_CASTLE_DOOR_UNUSED, castle_door_geo),
LOAD_MODEL_FROM_GEO(MODEL_CASTLE_WOODEN_DOOR_UNUSED, wooden_door_geo),
LOAD_MODEL_FROM_GEO(MODEL_CASTLE_DOOR_0_STARS,       castle_door_0_star_geo),
LOAD_MODEL_FROM_GEO(MODEL_CASTLE_DOOR_1_STAR,        castle_door_1_star_geo),
LOAD_MODEL_FROM_GEO(MODEL_CASTLE_DOOR_3_STARS,       castle_door_3_stars_geo),
LOAD_MODEL_FROM_GEO(MODEL_CASTLE_KEY_DOOR,           key_door_geo),
LOAD_MODEL_FROM_GEO(MODEL_CASTLE_STAR_DOOR_30_STARS, castle_geo_000F00),
LOAD_MODEL_FROM_GEO(MODEL_CASTLE_STAR_DOOR_8_STARS,  castle_geo_000F00),
LOAD_MODEL_FROM_GEO(MODEL_CASTLE_STAR_DOOR_50_STARS, castle_geo_000F00),
LOAD_MODEL_FROM_GEO(MODEL_CASTLE_STAR_DOOR_70_STARS, castle_geo_000F00),
""",
    'hmc':"""LOAD_MODEL_FROM_GEO(MODEL_HMC_WOODEN_DOOR,          wooden_door_geo),
LOAD_MODEL_FROM_GEO(MODEL_HMC_METAL_DOOR,           metal_door_geo),
LOAD_MODEL_FROM_GEO(MODEL_HMC_HAZY_MAZE_DOOR,       hazy_maze_door_geo),
LOAD_MODEL_FROM_GEO(MODEL_HMC_METAL_PLATFORM,       hmc_geo_0005A0),
LOAD_MODEL_FROM_GEO(MODEL_HMC_METAL_ARROW_PLATFORM, hmc_geo_0005B8),
LOAD_MODEL_FROM_GEO(MODEL_HMC_ELEVATOR_PLATFORM,    hmc_geo_0005D0),
LOAD_MODEL_FROM_GEO(MODEL_HMC_ROLLING_ROCK,         hmc_geo_000548),
LOAD_MODEL_FROM_GEO(MODEL_HMC_ROCK_PIECE,           hmc_geo_000570),
LOAD_MODEL_FROM_GEO(MODEL_HMC_ROCK_SMALL_PIECE,     hmc_geo_000588),
LOAD_MODEL_FROM_GEO(MODEL_HMC_RED_GRILLS,           hmc_geo_000530),
""",
    'ssl':"""LOAD_MODEL_FROM_GEO(MODEL_SSL_PALM_TREE,           palm_tree_geo),
LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_03,       ssl_geo_0005C0),
LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_04,       ssl_geo_0005D8),
LOAD_MODEL_FROM_GEO(MODEL_SSL_PYRAMID_TOP,         ssl_geo_000618),
LOAD_MODEL_FROM_GEO(MODEL_SSL_GRINDEL,             ssl_geo_000734),
LOAD_MODEL_FROM_GEO(MODEL_SSL_SPINDEL,             ssl_geo_000764),
LOAD_MODEL_FROM_GEO(MODEL_SSL_MOVING_PYRAMID_WALL, ssl_geo_000794),
LOAD_MODEL_FROM_GEO(MODEL_SSL_PYRAMID_ELEVATOR,    ssl_geo_0007AC),
LOAD_MODEL_FROM_GEO(MODEL_SSL_TOX_BOX,             ssl_geo_000630),
""",
    'bob':"""LOAD_MODEL_FROM_GEO(MODEL_BOB_BUBBLY_TREE,      bubbly_tree_geo),
    LOAD_MODEL_FROM_GEO(MODEL_BOB_CHAIN_CHOMP_GATE, bob_geo_000440),
    LOAD_MODEL_FROM_GEO(MODEL_BOB_SEESAW_PLATFORM,  bob_geo_000458),
    LOAD_MODEL_FROM_GEO(MODEL_BOB_BARS_GRILLS,      bob_geo_000470),
""",
    'sl':"""LOAD_MODEL_FROM_GEO(MODEL_SL_SNOW_TRIANGLE,      sl_geo_000390),
    LOAD_MODEL_FROM_GEO(MODEL_SL_CRACKED_ICE,        sl_geo_000360),
    LOAD_MODEL_FROM_GEO(MODEL_SL_CRACKED_ICE_CHUNK,  sl_geo_000378),
    LOAD_MODEL_FROM_GEO(MODEL_SL_SNOW_TREE,          snow_tree_geo),
""",
    'wdw':"""LOAD_MODEL_FROM_GEO(MODEL_WDW_BUBBLY_TREE,                   bubbly_tree_geo),
    LOAD_MODEL_FROM_GEO(MODEL_WDW_SQUARE_FLOATING_PLATFORM,      wdw_geo_000580),
    LOAD_MODEL_FROM_GEO(MODEL_WDW_ARROW_LIFT,                    wdw_geo_000598),
    LOAD_MODEL_FROM_GEO(MODEL_WDW_WATER_LEVEL_DIAMOND,           wdw_geo_0005C0),
    LOAD_MODEL_FROM_GEO(MODEL_WDW_HIDDEN_PLATFORM,               wdw_geo_0005E8),
    LOAD_MODEL_FROM_GEO(MODEL_WDW_EXPRESS_ELEVATOR,              wdw_geo_000610),
    LOAD_MODEL_FROM_GEO(MODEL_WDW_RECTANGULAR_FLOATING_PLATFORM, wdw_geo_000628),
    LOAD_MODEL_FROM_GEO(MODEL_WDW_ROTATING_PLATFORM,             wdw_geo_000640),
""",
    'jrb':"""LOAD_MODEL_FROM_GEO(MODEL_JRB_SHIP_LEFT_HALF_PART,  jrb_geo_000978),
    LOAD_MODEL_FROM_GEO(MODEL_JRB_SHIP_BACK_LEFT_PART,  jrb_geo_0009B0),
    LOAD_MODEL_FROM_GEO(MODEL_JRB_SHIP_RIGHT_HALF_PART, jrb_geo_0009E8),
    LOAD_MODEL_FROM_GEO(MODEL_JRB_SHIP_BACK_RIGHT_PART, jrb_geo_000A00),
    LOAD_MODEL_FROM_GEO(MODEL_JRB_SUNKEN_SHIP,          jrb_geo_000990),
    LOAD_MODEL_FROM_GEO(MODEL_JRB_SUNKEN_SHIP_BACK,     jrb_geo_0009C8),
    LOAD_MODEL_FROM_GEO(MODEL_JRB_ROCK,                 jrb_geo_000930),
    LOAD_MODEL_FROM_GEO(MODEL_JRB_SLIDING_BOX,          jrb_geo_000960),
    LOAD_MODEL_FROM_GEO(MODEL_JRB_FALLING_PILLAR,       jrb_geo_000900),
    LOAD_MODEL_FROM_GEO(MODEL_JRB_FALLING_PILLAR_BASE,  jrb_geo_000918),
    LOAD_MODEL_FROM_GEO(MODEL_JRB_FLOATING_PLATFORM,    jrb_geo_000948),
""",
    'thi':"""LOAD_MODEL_FROM_GEO(MODEL_THI_BUBBLY_TREE,     bubbly_tree_geo),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_03,   thi_geo_0005F0),
    LOAD_MODEL_FROM_GEO(MODEL_THI_WARP_PIPE,       warp_pipe_geo),
    LOAD_MODEL_FROM_GEO(MODEL_THI_HUGE_ISLAND_TOP, thi_geo_0005B0),
    LOAD_MODEL_FROM_GEO(MODEL_THI_TINY_ISLAND_TOP, thi_geo_0005C8),
""",
    'ttc':"""LOAD_MODEL_FROM_GEO(MODEL_TTC_ROTATING_CUBE,     ttc_geo_000240),
    LOAD_MODEL_FROM_GEO(MODEL_TTC_ROTATING_PRISM,    ttc_geo_000258),
    LOAD_MODEL_FROM_GEO(MODEL_TTC_PENDULUM,          ttc_geo_000270),
    LOAD_MODEL_FROM_GEO(MODEL_TTC_LARGE_TREADMILL,   ttc_geo_000288),
    LOAD_MODEL_FROM_GEO(MODEL_TTC_SMALL_TREADMILL,   ttc_geo_0002A8),
    LOAD_MODEL_FROM_GEO(MODEL_TTC_PUSH_BLOCK,        ttc_geo_0002C8),
    LOAD_MODEL_FROM_GEO(MODEL_TTC_ROTATING_HEXAGON,  ttc_geo_0002E0),
    LOAD_MODEL_FROM_GEO(MODEL_TTC_ROTATING_TRIANGLE, ttc_geo_0002F8),
    LOAD_MODEL_FROM_GEO(MODEL_TTC_PIT_BLOCK,         ttc_geo_000310),
    LOAD_MODEL_FROM_GEO(MODEL_TTC_PIT_BLOCK_UNUSED,  ttc_geo_000328),
    LOAD_MODEL_FROM_GEO(MODEL_TTC_ELEVATOR_PLATFORM, ttc_geo_000340),
    LOAD_MODEL_FROM_GEO(MODEL_TTC_CLOCK_HAND,        ttc_geo_000358),
    LOAD_MODEL_FROM_GEO(MODEL_TTC_SPINNER,           ttc_geo_000370),
    LOAD_MODEL_FROM_GEO(MODEL_TTC_SMALL_GEAR,        ttc_geo_000388),
    LOAD_MODEL_FROM_GEO(MODEL_TTC_LARGE_GEAR,        ttc_geo_0003A0),
""",
    'rr':"""LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_03,           rr_geo_000660),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_04,           rr_geo_000678),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_05,           rr_geo_000690),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_06,           rr_geo_0006A8),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_07,           rr_geo_0006C0),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_08,           rr_geo_0006D8),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_09,           rr_geo_0006F0),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_0A,           rr_geo_000708),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_0B,           rr_geo_000720),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_0C,           rr_geo_000738),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_0D,           rr_geo_000758),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_0E,           rr_geo_000770),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_0F,           rr_geo_000788),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_10,           rr_geo_0007A0),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_11,           rr_geo_0007B8),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_12,           rr_geo_0007D0),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_13,           rr_geo_0007E8),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_14,           rr_geo_000800),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_15,           rr_geo_000818),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_16,           rr_geo_000830),
    LOAD_MODEL_FROM_GEO(MODEL_RR_SLIDING_PLATFORM,         rr_geo_0008C0),
    LOAD_MODEL_FROM_GEO(MODEL_RR_FLYING_CARPET,            rr_geo_000848),
    LOAD_MODEL_FROM_GEO(MODEL_RR_OCTAGONAL_PLATFORM,       rr_geo_0008A8),
    LOAD_MODEL_FROM_GEO(MODEL_RR_ROTATING_BRIDGE_PLATFORM, rr_geo_000878),
    LOAD_MODEL_FROM_GEO(MODEL_RR_TRIANGLE_PLATFORM,        rr_geo_0008D8),
    LOAD_MODEL_FROM_GEO(MODEL_RR_CRUISER_WING,             rr_geo_000890),
    LOAD_MODEL_FROM_GEO(MODEL_RR_SEESAW_PLATFORM,          rr_geo_000908),
    LOAD_MODEL_FROM_GEO(MODEL_RR_L_SHAPED_PLATFORM,        rr_geo_000940),
    LOAD_MODEL_FROM_GEO(MODEL_RR_SWINGING_PLATFORM,        rr_geo_000860),
    LOAD_MODEL_FROM_GEO(MODEL_RR_DONUT_PLATFORM,           rr_geo_000920),
    LOAD_MODEL_FROM_GEO(MODEL_RR_ELEVATOR_PLATFORM,        rr_geo_0008F0),
    LOAD_MODEL_FROM_GEO(MODEL_RR_TRICKY_TRIANGLES,         rr_geo_000958),
    LOAD_MODEL_FROM_GEO(MODEL_RR_TRICKY_TRIANGLES_FRAME1,  rr_geo_000970),
    LOAD_MODEL_FROM_GEO(MODEL_RR_TRICKY_TRIANGLES_FRAME2,  rr_geo_000988),
    LOAD_MODEL_FROM_GEO(MODEL_RR_TRICKY_TRIANGLES_FRAME3,  rr_geo_0009A0),
    LOAD_MODEL_FROM_GEO(MODEL_RR_TRICKY_TRIANGLES_FRAME4,  rr_geo_0009B8),
""",
    "castle_grounds":"""LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_03,           castle_grounds_geo_0006F4),
    LOAD_MODEL_FROM_GEO(MODEL_CASTLE_GROUNDS_BUBBLY_TREE,  bubbly_tree_geo),
    LOAD_MODEL_FROM_GEO(MODEL_CASTLE_GROUNDS_WARP_PIPE,    warp_pipe_geo),
    LOAD_MODEL_FROM_GEO(MODEL_CASTLE_GROUNDS_CASTLE_DOOR,  castle_door_geo),
    LOAD_MODEL_FROM_GEO(MODEL_CASTLE_GROUNDS_METAL_DOOR,   metal_door_geo),
    LOAD_MODEL_FROM_GEO(MODEL_CASTLE_GROUNDS_VCUTM_GRILL,  castle_grounds_geo_00070C),
    LOAD_MODEL_FROM_GEO(MODEL_CASTLE_GROUNDS_FLAG,         castle_grounds_geo_000660),
    LOAD_MODEL_FROM_GEO(MODEL_CASTLE_GROUNDS_CANNON_GRILL, castle_grounds_geo_000724),
""",
    'bitdw':"""LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_03,       geo_bitdw_0003C0),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_04,       geo_bitdw_0003D8),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_05,       geo_bitdw_0003F0),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_06,       geo_bitdw_000408),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_07,       geo_bitdw_000420),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_08,       geo_bitdw_000438),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_09,       geo_bitdw_000450),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_0A,       geo_bitdw_000468),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_0B,       geo_bitdw_000480),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_0C,       geo_bitdw_000498),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_0D,       geo_bitdw_0004B0),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_0E,       geo_bitdw_0004C8),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_0F,       geo_bitdw_0004E0),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_10,       geo_bitdw_0004F8),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_11,       geo_bitdw_000510),
    LOAD_MODEL_FROM_GEO(MODEL_BITDW_WARP_PIPE,         warp_pipe_geo),
    LOAD_MODEL_FROM_GEO(MODEL_BITDW_SQUARE_PLATFORM,   geo_bitdw_000558),
    LOAD_MODEL_FROM_GEO(MODEL_BITDW_SEESAW_PLATFORM,   geo_bitdw_000540),
    LOAD_MODEL_FROM_GEO(MODEL_BITDW_SLIDING_PLATFORM,  geo_bitdw_000528),
    LOAD_MODEL_FROM_GEO(MODEL_BITDW_FERRIS_WHEEL_AXLE, geo_bitdw_000570),
    LOAD_MODEL_FROM_GEO(MODEL_BITDW_BLUE_PLATFORM,     geo_bitdw_000588),
    LOAD_MODEL_FROM_GEO(MODEL_BITDW_STAIRCASE_FRAME4,  geo_bitdw_0005A0),
    LOAD_MODEL_FROM_GEO(MODEL_BITDW_STAIRCASE_FRAME3,  geo_bitdw_0005B8),
    LOAD_MODEL_FROM_GEO(MODEL_BITDW_STAIRCASE_FRAME2,  geo_bitdw_0005D0),
    LOAD_MODEL_FROM_GEO(MODEL_BITDW_STAIRCASE_FRAME1,  geo_bitdw_0005E8),
    LOAD_MODEL_FROM_GEO(MODEL_BITDW_STAIRCASE,         geo_bitdw_000600),
""",
    'vcutm':"""LOAD_MODEL_FROM_GEO(MODEL_VCUTM_SEESAW_PLATFORM, vcutm_geo_0001F0),
""",
    'bitfs':"""LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_03,             bitfs_geo_0004B0),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_04,             bitfs_geo_0004C8),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_05,             bitfs_geo_0004E0),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_06,             bitfs_geo_0004F8),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_07,             bitfs_geo_000510),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_08,             bitfs_geo_000528),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_09,             bitfs_geo_000540),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_0A,             bitfs_geo_000558),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_0B,             bitfs_geo_000570),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_0C,             bitfs_geo_000588),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_0D,             bitfs_geo_0005A0),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_0E,             bitfs_geo_0005B8),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_0F,             bitfs_geo_0005D0),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_10,             bitfs_geo_0005E8),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_11,             bitfs_geo_000600),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_12,             bitfs_geo_000618),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_13,             bitfs_geo_000630),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_14,             bitfs_geo_000648),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_15,             bitfs_geo_000660),
    LOAD_MODEL_FROM_GEO(MODEL_BITFS_PLATFORM_ON_TRACK,       bitfs_geo_000758),
    LOAD_MODEL_FROM_GEO(MODEL_BITFS_TILTING_SQUARE_PLATFORM, bitfs_geo_0006C0),
    LOAD_MODEL_FROM_GEO(MODEL_BITFS_SINKING_PLATFORMS,       bitfs_geo_000770),
    LOAD_MODEL_FROM_GEO(MODEL_BITFS_BLUE_POLE,               bitfs_geo_0006A8),
    LOAD_MODEL_FROM_GEO(MODEL_BITFS_SINKING_CAGE_PLATFORM,   bitfs_geo_000690),
    LOAD_MODEL_FROM_GEO(MODEL_BITFS_ELEVATOR,                bitfs_geo_000678),
    LOAD_MODEL_FROM_GEO(MODEL_BITFS_STRETCHING_PLATFORMS,    bitfs_geo_000708),
    LOAD_MODEL_FROM_GEO(MODEL_BITFS_SEESAW_PLATFORM,         bitfs_geo_000788),
    LOAD_MODEL_FROM_GEO(MODEL_BITFS_MOVING_SQUARE_PLATFORM,  bitfs_geo_000728),
    LOAD_MODEL_FROM_GEO(MODEL_BITFS_SLIDING_PLATFORM,        bitfs_geo_000740),
    LOAD_MODEL_FROM_GEO(MODEL_BITFS_TUMBLING_PLATFORM_PART,  bitfs_geo_0006D8),
    LOAD_MODEL_FROM_GEO(MODEL_BITFS_TUMBLING_PLATFORM,       bitfs_geo_0006F0),
""",
    'bits':"""LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_03,           bits_geo_000430),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_04,           bits_geo_000448),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_05,           bits_geo_000460),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_06,           bits_geo_000478),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_07,           bits_geo_000490),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_08,           bits_geo_0004A8),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_09,           bits_geo_0004C0),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_0A,           bits_geo_0004D8),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_0B,           bits_geo_0004F0),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_0C,           bits_geo_000508),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_0D,           bits_geo_000520),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_0E,           bits_geo_000538),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_0F,           bits_geo_000550),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_10,           bits_geo_000568),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_11,           bits_geo_000580),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_12,           bits_geo_000598),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_13,           bits_geo_0005B0),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_14,           bits_geo_0005C8),
    LOAD_MODEL_FROM_GEO(MODEL_BITS_SLIDING_PLATFORM,       bits_geo_0005E0),
    LOAD_MODEL_FROM_GEO(MODEL_BITS_TWIN_SLIDING_PLATFORMS, bits_geo_0005F8),
    LOAD_MODEL_FROM_GEO(MODEL_BITS_OCTAGONAL_PLATFORM,     bits_geo_000610),
    LOAD_MODEL_FROM_GEO(MODEL_BITS_BLUE_PLATFORM,          bits_geo_000628),
    LOAD_MODEL_FROM_GEO(MODEL_BITS_FERRIS_WHEEL_AXLE,      bits_geo_000640),
    LOAD_MODEL_FROM_GEO(MODEL_BITS_ARROW_PLATFORM,         bits_geo_000658),
    LOAD_MODEL_FROM_GEO(MODEL_BITS_SEESAW_PLATFORM,        bits_geo_000670),
    LOAD_MODEL_FROM_GEO(MODEL_BITS_TILTING_W_PLATFORM,     bits_geo_000688),
    LOAD_MODEL_FROM_GEO(MODEL_BITS_STAIRCASE,              bits_geo_0006A0),
    LOAD_MODEL_FROM_GEO(MODEL_BITS_STAIRCASE_FRAME1,       bits_geo_0006B8),
    LOAD_MODEL_FROM_GEO(MODEL_BITS_STAIRCASE_FRAME2,       bits_geo_0006D0),
    LOAD_MODEL_FROM_GEO(MODEL_BITS_STAIRCASE_FRAME3,       bits_geo_0006E8),
    LOAD_MODEL_FROM_GEO(MODEL_BITS_STAIRCASE_FRAME4,       bits_geo_000700),
""",
    'lll':"""LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_03,                  lll_geo_0009E0),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_04,                  lll_geo_0009F8),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_05,                  lll_geo_000A10),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_06,                  lll_geo_000A28),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_07,                  lll_geo_000A40),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_08,                  lll_geo_000A60),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_0A,                  lll_geo_000A90),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_0B,                  lll_geo_000AA8),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_0C,                  lll_geo_000AC0),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_0D,                  lll_geo_000AD8),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_0E,                  lll_geo_000AF0),
    LOAD_MODEL_FROM_GEO(MODEL_LLL_DRAWBRIDGE_PART,                lll_geo_000B20),
    LOAD_MODEL_FROM_GEO(MODEL_LLL_ROTATING_BLOCK_FIRE_BARS,       lll_geo_000B38),
    LOAD_MODEL_FROM_GEO(MODEL_LLL_ROTATING_HEXAGONAL_RING,        lll_geo_000BB0),
    LOAD_MODEL_FROM_GEO(MODEL_LLL_SINKING_RECTANGULAR_PLATFORM,   lll_geo_000BC8),
    LOAD_MODEL_FROM_GEO(MODEL_LLL_SINKING_SQUARE_PLATFORMS,       lll_geo_000BE0),
    LOAD_MODEL_FROM_GEO(MODEL_LLL_TILTING_SQUARE_PLATFORM,        lll_geo_000BF8),
    LOAD_MODEL_FROM_GEO(MODEL_LLL_BOWSER_PIECE_1,                 lll_geo_000C10),
    LOAD_MODEL_FROM_GEO(MODEL_LLL_BOWSER_PIECE_2,                 lll_geo_000C30),
    LOAD_MODEL_FROM_GEO(MODEL_LLL_BOWSER_PIECE_3,                 lll_geo_000C50),
    LOAD_MODEL_FROM_GEO(MODEL_LLL_BOWSER_PIECE_4,                 lll_geo_000C70),
    LOAD_MODEL_FROM_GEO(MODEL_LLL_BOWSER_PIECE_5,                 lll_geo_000C90),
    LOAD_MODEL_FROM_GEO(MODEL_LLL_BOWSER_PIECE_6,                 lll_geo_000CB0),
    LOAD_MODEL_FROM_GEO(MODEL_LLL_BOWSER_PIECE_7,                 lll_geo_000CD0),
    LOAD_MODEL_FROM_GEO(MODEL_LLL_BOWSER_PIECE_8,                 lll_geo_000CF0),
    LOAD_MODEL_FROM_GEO(MODEL_LLL_BOWSER_PIECE_9,                 lll_geo_000D10),
    LOAD_MODEL_FROM_GEO(MODEL_LLL_BOWSER_PIECE_10,                lll_geo_000D30),
    LOAD_MODEL_FROM_GEO(MODEL_LLL_BOWSER_PIECE_11,                lll_geo_000D50),
    LOAD_MODEL_FROM_GEO(MODEL_LLL_BOWSER_PIECE_12,                lll_geo_000D70),
    LOAD_MODEL_FROM_GEO(MODEL_LLL_BOWSER_PIECE_13,                lll_geo_000D90),
    LOAD_MODEL_FROM_GEO(MODEL_LLL_BOWSER_PIECE_14,                lll_geo_000DB0),
    LOAD_MODEL_FROM_GEO(MODEL_LLL_MOVING_OCTAGONAL_MESH_PLATFORM, lll_geo_000B08),
    LOAD_MODEL_FROM_GEO(MODEL_LLL_SINKING_ROCK_BLOCK,             lll_geo_000DD0),
    LOAD_MODEL_FROM_GEO(MODEL_LLL_ROLLING_LOG,                    lll_geo_000DE8),
    LOAD_MODEL_FROM_GEO(MODEL_LLL_ROTATING_HEXAGONAL_PLATFORM,    lll_geo_000A78),
    LOAD_MODEL_FROM_GEO(MODEL_LLL_WOOD_BRIDGE,                    lll_geo_000B50),
    LOAD_MODEL_FROM_GEO(MODEL_LLL_LARGE_WOOD_BRIDGE,              lll_geo_000B68),
    LOAD_MODEL_FROM_GEO(MODEL_LLL_FALLING_PLATFORM,               lll_geo_000B80),
    LOAD_MODEL_FROM_GEO(MODEL_LLL_LARGE_FALLING_PLATFORM,         lll_geo_000B98),
    LOAD_MODEL_FROM_GEO(MODEL_LLL_VOLCANO_FALLING_TRAP,           lll_geo_000EA8),
""",
    'ddd':"""LOAD_MODEL_FROM_GEO(MODEL_DDD_BOWSER_SUB_DOOR, ddd_geo_000478),
    LOAD_MODEL_FROM_GEO(MODEL_DDD_BOWSER_SUB,      ddd_geo_0004A0),
    LOAD_MODEL_FROM_GEO(MODEL_DDD_POLE,            ddd_geo_000450),
""",
    'wf':"""LOAD_MODEL_FROM_GEO(MODEL_WF_BUBBLY_TREE,                   bubbly_tree_geo),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_03,                wf_geo_0007E0),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_04,                wf_geo_000820),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_05,                wf_geo_000860),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_06,                wf_geo_000878),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_07,                wf_geo_000890),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_08,                wf_geo_0008A8),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_09,                wf_geo_0008E8),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_0A,                wf_geo_000900),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_0C,                wf_geo_000940),
    LOAD_MODEL_FROM_GEO(MODEL_WF_GIANT_POLE,                    wf_geo_000AE0),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_0E,                wf_geo_000958),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_0F,                wf_geo_0009A0),
    LOAD_MODEL_FROM_GEO(MODEL_WF_ROTATING_PLATFORM,             wf_geo_0009B8),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_11,                wf_geo_0009D0),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_12,                wf_geo_0009E8),
    LOAD_MODEL_FROM_GEO(MODEL_WF_SMALL_BOMP,                    wf_geo_000A00),
    LOAD_MODEL_FROM_GEO(MODEL_WF_LARGE_BOMP,                    wf_geo_000A40),
    LOAD_MODEL_FROM_GEO(MODEL_WF_ROTATING_WOODEN_PLATFORM,      wf_geo_000A58),
    LOAD_MODEL_FROM_GEO(MODEL_WF_SLIDING_PLATFORM,              wf_geo_000A98),
    LOAD_MODEL_FROM_GEO(MODEL_WF_TUMBLING_BRIDGE_PART,          wf_geo_000AB0),
    LOAD_MODEL_FROM_GEO(MODEL_WF_TUMBLING_BRIDGE,               wf_geo_000AC8),
    LOAD_MODEL_FROM_GEO(MODEL_WF_TOWER_TRAPEZOID_PLATORM,       wf_geo_000AF8),
    LOAD_MODEL_FROM_GEO(MODEL_WF_TOWER_SQUARE_PLATORM,          wf_geo_000B10),
    LOAD_MODEL_FROM_GEO(MODEL_WF_TOWER_SQUARE_PLATORM_UNUSED,   wf_geo_000B38),
    LOAD_MODEL_FROM_GEO(MODEL_WF_TOWER_SQUARE_PLATORM_ELEVATOR, wf_geo_000B60),
    LOAD_MODEL_FROM_GEO(MODEL_WF_BREAKABLE_WALL_RIGHT,          wf_geo_000B78),
    LOAD_MODEL_FROM_GEO(MODEL_WF_BREAKABLE_WALL_LEFT,           wf_geo_000B90),
    LOAD_MODEL_FROM_GEO(MODEL_WF_KICKABLE_BOARD,                wf_geo_000BA8),
    LOAD_MODEL_FROM_GEO(MODEL_WF_TOWER_DOOR,                    wf_geo_000BE0),
    LOAD_MODEL_FROM_GEO(MODEL_WF_KICKABLE_BOARD_FELLED,         wf_geo_000BC8),
""",
    'castle_courtyard':"""LOAD_MODEL_FROM_GEO(MODEL_COURTYARD_SPIKY_TREE,  spiky_tree_geo),
    LOAD_MODEL_FROM_GEO(MODEL_COURTYARD_WOODEN_DOOR, wooden_door_geo),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_03,     castle_courtyard_geo_000200),
""",
    'bowser_2':"""LOAD_MODEL_FROM_GEO(MODEL_BOWSER_2_TILTING_ARENA, bowser_2_geo_000170),
""",
    'bowser_3':"""LOAD_MODEL_FROM_GEO(MODEL_BOWSER_3_FALLING_PLATFORM_1,  bowser_3_geo_000290),
    LOAD_MODEL_FROM_GEO(MODEL_BOWSER_3_FALLING_PLATFORM_2,  bowser_3_geo_0002A8),
    LOAD_MODEL_FROM_GEO(MODEL_BOWSER_3_FALLING_PLATFORM_3,  bowser_3_geo_0002C0),
    LOAD_MODEL_FROM_GEO(MODEL_BOWSER_3_FALLING_PLATFORM_4,  bowser_3_geo_0002D8),
    LOAD_MODEL_FROM_GEO(MODEL_BOWSER_3_FALLING_PLATFORM_5,  bowser_3_geo_0002F0),
    LOAD_MODEL_FROM_GEO(MODEL_BOWSER_3_FALLING_PLATFORM_6,  bowser_3_geo_000308),
    LOAD_MODEL_FROM_GEO(MODEL_BOWSER_3_FALLING_PLATFORM_7,  bowser_3_geo_000320),
    LOAD_MODEL_FROM_GEO(MODEL_BOWSER_3_FALLING_PLATFORM_8,  bowser_3_geo_000338),
    LOAD_MODEL_FROM_GEO(MODEL_BOWSER_3_FALLING_PLATFORM_9,  bowser_3_geo_000350),
    LOAD_MODEL_FROM_GEO(MODEL_BOWSER_3_FALLING_PLATFORM_10, bowser_3_geo_000368),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_03,            bowser_3_geo_000380),
""",
    'ttm':"""LOAD_MODEL_FROM_GEO(MODEL_TTM_SLIDE_EXIT_PODIUM, ttm_geo_000DF4),
    LOAD_MODEL_FROM_GEO(MODEL_TTM_ROLLING_LOG,       ttm_geo_000730),
    LOAD_MODEL_FROM_GEO(MODEL_TTM_STAR_CAGE,        ttm_geo_000710),
    LOAD_MODEL_FROM_GEO(MODEL_TTM_BLUE_SMILEY,       ttm_geo_000D14),
    LOAD_MODEL_FROM_GEO(MODEL_TTM_YELLOW_SMILEY,     ttm_geo_000D4C),
    LOAD_MODEL_FROM_GEO(MODEL_TTM_STAR_SMILEY,       ttm_geo_000D84),
    LOAD_MODEL_FROM_GEO(MODEL_TTM_MOON_SMILEY,       ttm_geo_000DBC),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_03,     ttm_geo_000748),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_04,     ttm_geo_000778),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_05,     ttm_geo_0007A8),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_06,     ttm_geo_0007D8),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_07,     ttm_geo_000808),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_08,     ttm_geo_000830),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_09,     ttm_geo_000858),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_0A,     ttm_geo_000880),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_0B,     ttm_geo_0008A8),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_0C,     ttm_geo_0008D0),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_0D,     ttm_geo_0008F8),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_0F,     ttm_geo_000920),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_10,     ttm_geo_000948),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_11,     ttm_geo_000970),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_12,     ttm_geo_000990),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_13,     ttm_geo_0009C0),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_14,     ttm_geo_0009F0),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_15,     ttm_geo_000A18),
    LOAD_MODEL_FROM_GEO(MODEL_LEVEL_GEOMETRY_16,     ttm_geo_000A40),
"""
}

scriptHeader='''#include <ultra64.h>
#include "sm64.h"
#include "behavior_data.h"
#include "model_ids.h"
#include "seq_ids.h"
#include "dialog_ids.h"
#include "segment_symbols.h"
#include "level_commands.h"
#include "game/level_update.h"
#include "levels/scripts.h"
#include "actors/common1.h"
#include "make_const_nonconst.h"

'''

geocHeader='''#include <ultra64.h>
#include "sm64.h"
#include "geo_commands.h"
#include "game/level_geo.h"
#include "game/geo_misc.h"
#include "game/camera.h"
#include "game/moving_texture.h"
#include "game/screen_transition.h"
#include "game/paintings.h"
#include "make_const_nonconst.h"

'''

ldHeader='''#include <ultra64.h>
#include "sm64.h"
#include "surface_terrains.h"
#include "moving_texture_macros.h"
#include "level_misc_macros.h"
#include "macro_preset_names.h"
#include "special_preset_names.h"
#include "textures.h"
#include "dialog_ids.h"

#include "make_const_nonconst.h"

'''

class Script():
	def __init__(self,level):
		self.map = open('sm64.us.map','r')
		self.map=self.map.readlines()
		self.banks=[None for a in range(32)]
		self.asm=[[0x80400000,0x1200000,0x1220000]]
		self.models=[None for a in range(256)]
		self.Currlevel=level
		self.levels={}
		self.levels[self.Currlevel]=[None for a in range(8)]
		#stack is simply a stack of ptrs
		#base is the prev pos
		#top is the current pos
		self.Base=None
		self.Stack=[]
		self.Top=-1
		self.CurrArea=None
		self.header=[]
	def B2P(self,B):
		Bank=B>>24
		offset=B&0xFFFFFF
		seg = self.banks[Bank]
		if not seg:
			# print(hex(B),hex(Bank),self.banks[Bank-2:Bank+3])
			raise ''
		return seg[0]+offset
	def L4B(self,T):
		x=0
		for i,b in enumerate(T):
			x+=b<<(8*(3-i))
		return x
	def GetArea(self):
		try:
			return self.levels[self.Currlevel][self.CurrArea]
		except:
			return None
	def GetNumAreas(self,level):
		count=[]
		for i,area in enumerate(self.levels[level]):
			if area:
				count.append(i)
		return count
	def GetLabel(self,addr):
		#behavior is in bank 0 and won't be in map ever
		if len(addr)==6:
			return '0x'+addr
		for l in self.map:
			if addr in l:
				q= l.rfind(" ")
				return l[q:-1]
		return "0x"+addr
	def RME(self,num,rom):
		if self.editor:
			return
		start=self.B2P(0x19005f00)
		start=TcH(rom[start+num*16:start+num*16+4])
		end=TcH(rom[start+4+num*16:start+num*16+8])
		self.banks[0x0e]=[start,end]
	def MakeDec(self,name):
		self.header.append(name)
	def Seg2(self,rom):
		UPH = (lambda x,y: struct.unpack(">H",x[y:y+2])[0])
		start=UPH(rom,0x3ac2)<<16
		start+=UPH(rom,0x3acE)
		end=UPH(rom,0x3ac6)<<16
		end+=UPH(rom,0x3acA)
		self.banks[2]=[start,end]

class Area():
		def __init__(self):
			pass

#tuple convert to hex
def TcH(bytes):
	a = struct.pack(">%dB"%len(bytes),*bytes)
	if len(bytes)==4:
		return struct.unpack(">L",a)[0]
	if len(bytes)==2:
		return struct.unpack(">H",a)[0]
	if len(bytes)==1:
		return struct.unpack(">B",a)[0]

def U2S(half):
	return struct.unpack(">h",struct.pack(">H",half))[0]

def LoadRawJumpPush(rom,cmd,start,script):
	arg=cmd[2]
	bank=arg[0:2]
	begin = arg[2:6]
	end = arg[6:10]
	jump = arg[10:14]
	script.banks[TcH(bank)]=[TcH(begin),TcH(end)]
	script.Stack.append(start)
	script.Top+=1
	script.Stack.append(script.Base)
	script.Top+=1
	script.Base=script.Top
	return script.B2P(TcH(jump))

def LoadRawJump(rom,cmd,start,script):
	arg=cmd[2]
	bank=arg[0:2]
	begin = arg[2:6]
	end = arg[6:10]
	jump = arg[10:14]
	script.banks[TcH(bank)]=[TcH(begin),TcH(end)]
	script.Top=script.Base
	return script.B2P(TcH(jump))

def Exit(rom,cmd,start,script):
	script.Top=script.Base
	script.Base=script.Stack[script.Top]
	script.Stack.pop()
	script.Top-=1
	start=script.Stack[script.Top]
	script.Stack.pop()
	script.Top-=1
	return start
	
def JumpRaw(rom,cmd,start,script):
	arg=cmd[2]
	return script.B2P(TcH(arg[2:6]))
	
def JumpPush(rom,cmd,start,script):
	script.Top+=1
	script.Stack.append(start)
	arg=cmd[2]
	return script.B2P(TcH(arg[2:6]))
	
def Pop(rom,cmd,start,script):
	start=script.Stack[script.Top]
	script.Top-=1
	script.Stack.pop()
	return start
	
def CondPop(rom,cmd,start,script):
	#this is where the script loops
	#Ill assume no custom shit is done
	#meaning this will always signal end of level
	return None

def CondJump(rom,cmd,start,script):
	arg=cmd[2]
	level=arg[2:6]
	jump=arg[6:10]
	if script.Currlevel==TcH(level):
		return script.B2P(TcH(jump))
	else:
		return start
	
def SetLevel(rom,cmd,start,script):
	#gonna ignore this and take user input instead
	#script.Currlevel=TcH(cmd[2])
	# if not script.levels.get("Currlevel"):
		# script.levels[script.Currlevel]=[None for a in range(8)]
	return start
	
def LoadAsm(rom,cmd,start,script):
	arg=cmd[2]
	ram=arg[2:6]
	begin=arg[6:10]
	end=arg[10:14]
	Q=[TcH(ram),TcH(begin),TcH(end)]
	if Q not in script.asm:
		script.asm.append(Q)
	return start

def LoadData(rom,cmd,start,script):
	arg=cmd[2]
	bank=arg[1:2]
	begin = arg[2:6]
	end = arg[6:10]
	script.banks[TcH(bank)]=[TcH(begin),TcH(end)]
	return start

def LoadMio0(rom,cmd,start,script):
	pass
	
def LoadMio0Tex(rom,cmd,start,script):
	return LoadData(rom,cmd,start,script)

def StartArea(rom,cmd,start,script):
	#ignore stuff in bank 0x14 because thats star select/file select and messes up export
	arg=cmd[2]
	if TcH(arg[2:3])==0x14:
		return start
	area=arg[0]+script.Aoffset
	script.CurrArea=area
	q=Area()
	q.geo=TcH(arg[2:6])
	q.objects=[]
	q.warps=[]
	q.rom=rom
	script.levels[script.Currlevel][script.CurrArea]=q
	return start
	
def EndArea(rom,cmd,start,script):
	script.CurrArea=None
	return start
	
def LoadPolyF3d(rom,cmd,start,script):
	arg=cmd[2]
	id=arg[1:2]
	layer=TcH(arg[0:1])>>4
	f3d=TcH(arg[2:6])
	script.models[TcH(id)]=(f3d,'f3d',layer)
	return start
	
def LoadPolyGeo(rom,cmd,start,script):
	arg=cmd[2]
	id=arg[1:2]
	geo=TcH(arg[2:6])
	script.models[TcH(id)]=(geo,'geo')
	return start
	
def PlaceObject(rom,cmd,start,script):
	arg=cmd[2]
	A=script.GetArea()
	if not A:
		return start
	mask=arg[0]
	#remove disabled objects
	if mask==0:
		return start
	id=arg[1]
	#efficiency
	x=U2S(TcH(arg[2:4]))
	y=U2S(TcH(arg[4:6]))
	z=U2S(TcH(arg[6:8]))
	rx=U2S(TcH(arg[8:10]))
	ry=U2S(TcH(arg[10:12]))
	rz=U2S(TcH(arg[12:14]))
	bparam=hex(TcH(arg[14:18]))
	bhv=script.GetLabel(hex(TcH(arg[18:22]))[2:])
	#print(bhv)
	PO=(id,x,y,z,rx,ry,rz,bparam,bhv,mask)
	A.objects.append(PO)
	return start
	
def PlaceMario(rom,cmd,start,script):
	#do nothing
	return start

def ConnectWarp(rom,cmd,start,script):
	A=script.GetArea()
	if not A:
		return start
	arg=cmd[2]
	W=(arg[0],arg[1],arg[2]+script.Aoffset,arg[3],arg[4])
	A.warps.append(W)
	return start
	
def PaintingWarp(rom,cmd,start,script):
	return start
	
def InstantWarp(rom,cmd,start,script):
	return start
	
def SetMarioDefault(rom,cmd,start,script):
	arg=cmd[2]
	script.mStart = [arg[0],U2S(TcH(arg[2:4])),U2S(TcH(arg[4:6])),U2S(TcH(arg[6:8])),U2S(TcH(arg[8:10]))]
	return start
	
def LoadCol(rom,cmd,start,script):
	arg=cmd[2]
	col=TcH(arg[2:6])
	A=script.GetArea()
	if not A:
		return start
	A.col=col
	return start
	
def LoadRoom(rom,cmd,start,script):
	return start

def SetDialog(rom,cmd,start,script):
	return start

def SetMusic(rom,cmd,start,script):
	A=script.GetArea()
	if A:
		arg=cmd[2]
		A.music=TcH(arg[3:4])
	return start

def SetMusic2(rom,cmd,start,script):
	A=script.GetArea()
	if A:
		arg=cmd[2]
		A.music=TcH(arg[1:2])
	return start

def SetTerrain(rom,cmd,start,script):
	A=script.GetArea()
	if A:
		arg=cmd[2]
		A.terrain=TcH(arg[1:2])
	return start

def ULC(rom,start):
	cmd = struct.unpack(">B",rom[start:start+1])[0]
	len = struct.unpack(">B",rom[start+1:start+2])[0]
	q=len-2
	args = struct.unpack(">%dB"%q,rom[start+2:start+len])
	return [cmd,len,args]

#iterates through script until a cmd is found that
#requires new action, then returns that cmd
def PLC(rom,start):
	(cmd,len,args) = ULC(rom,start)
	start+=len
	if cmd in jumps:
		return (cmd,len,args,start)
	return PLC(rom,start)

def WriteGeo(rom,s,num,name):
	(geo,dls,WB,envfx)=GW.GeoParse(rom,s.B2P(s.models[num][0]),s,s.models[num][0],"actor_"+str(num)+"_")
	#write geo layout file
	GW.GeoWrite(geo,name/'geo.inc.c',"actor_"+str(num)+"_")
	return dls

def WriteModel(rom,dls,s,name,Hname,id,tdir):
	x=0
	ModelData=[]
	while(x<len(dls)):
		#check for bad ptr
		st=dls[x][0]
		first=TcH(rom[st:st+4])
		c=rom[st]
		if first==0x01010101 or not F3D.DecodeFmt.get(c):
			return
		(dl,verts,textures,amb,diff,jumps,ranges)=F3D.DecodeDL(rom,dls[x],s,id)
		ModelData.append([dls[x],dl,verts,textures,amb,diff,ranges])
		for jump in jumps:
			if jump not in dls:
				dls.append(jump)
		x+=1
	refs = F3D.ModelWrite(rom,ModelData,name,id,tdir)
	modelH = name/'model.inc.h'
	mh = open(modelH,'w')
	headgaurd="%s_HEADER_H"%(Hname)
	mh.write('#ifndef %s\n#define %s\n#include "types.h"\n'%(headgaurd,headgaurd))
	for r in refs:
		mh.write('extern '+r+';\n')
	mh.write("#endif")
	mh.close()
	return dls

def ClosestIntinDict(num,dict):
	min=0xFFFFFFFFFFFFFF
	res = None
	for k,v in dict.items():
		if abs(k-num)<min:
			min=abs(k-num)
			res = v
	return res

def InsertBankLoads(s,f):
	banks = [s.banks[10],s.banks[15],s.banks[12],s.banks[13]]
	for i,b in enumerate(banks):
		if not i:
			d=skyboxes
		else:
			d=actors
		if b:
			banks[i]=ClosestIntinDict(b[0],d)
			if not i:
				load = "LOAD_MIO0(0xA,"+banks[i]+"SegmentRomStart,"+banks[i]+"SegmentRomEnd),\n"
			else:
				load = "LOAD_MIO0(%d,"%banks[i][1]+banks[i][0]+"_mio0SegmentRomStart,"+banks[i][0]+"_mio0SegmentRomEnd),\n"
				load += "LOAD_RAW(%d,"%banks[i][2]+banks[i][0]+"_geoSegmentRomStart,"+banks[i][0]+"_geoSegmentRomEnd),\n"
			f.write(load)
	return banks

def DetLevelSpecBank(s,f):
	level = None
	if s.banks[7]:
		level =ClosestIntinDict(s.banks[7][0],LevelSpecificBanks)
	return level

def WriteLevelScript(name,Lnum,s,level,Anum,envfx):
	f = open(name,'w')
	f.write(scriptHeader)
	f.write('#include "levels/%s/header.h"\n'%Lnum)
	#This is the ideal to match hacks, but currently the way the linker is
	#setup, level object data is in the same bank as level mesh so this cannot be done.
	# LoadLevel = DetLevelSpecBank(s,f)
	if LoadLevel and LoadLevel!=Lnum:
		f.write('//#include "levels/%s/header.h" This is necessary because this level uses level specific objects from another level\n'%LoadLevel)
	f.write('const LevelScript level_%s_entry[] = {\n'%Lnum)
	#entry stuff
	f.write("INIT_LEVEL(),\n")
	if LoadLevel:
		f.write("// LOAD_MIO0(0x07, _"+LoadLevel+"_segment_7SegmentRomStart, _"+LoadLevel+"_segment_7SegmentRomEnd), This will not work if added but is present in original level\n")
	# else:
	f.write("LOAD_MIO0(0x07, _"+Lnum+"_segment_7SegmentRomStart, _"+Lnum+"_segment_7SegmentRomEnd),\n")
	if envfx:
		f.write("LOAD_MIO0(        /*seg*/ 0x0B, _effect_mio0SegmentRomStart, _effect_mio0SegmentRomEnd),\n")
	#add in loaded banks
	banks = InsertBankLoads(s,f)
	f.write("ALLOC_LEVEL_POOL(),\nMARIO(/*model*/ MODEL_MARIO, /*behParam*/ 0x00000001, /*beh*/ bhvMario),\nLOAD_MODEL_FROM_GEO(22, warp_pipe_geo),\n")
	# if LoadLevel:
		# f.write(LevelSpecificModels[LoadLevel])
	#add in jumps based on banks returned
	for b in banks:
		if type(b)==list:
			f.write("JUMP_LINK("+b[3]+"),\n")
	#a bearable amount of cringe
	for a in Anum:
		id = Lnum+"_"+str(a)+"_"
		f.write('JUMP_LINK(local_area_%s),\n'%id)
	#end script
	f.write("FREE_LEVEL_POOL(),\n")
	f.write("MARIO_POS({},{},{},{},{}),\n".format(*s.mStart))
	f.write("CALL(/*arg*/ 0, /*func*/ lvl_init_or_update),\nCALL_LOOP(/*arg*/ 1, /*func*/ lvl_init_or_update),\nCLEAR_LEVEL(),\nSLEEP_BEFORE_EXIT(/*frames*/ 1),\nEXIT(),\n};\n")
	for a in Anum:
		id = Lnum+"_"+str(a)+"_"
		area=level[a]
		WriteArea(f,s,area,a,id)

def WriteArea(f,s,area,Anum,id):
	#begin area
	ascript = "const LevelScript local_area_%s[]"%id
	f.write(ascript+' = {\n')
	s.MakeDec(ascript)
	Gptr='Geo_'+id+hex(area.geo)
	f.write("AREA(%d,%s),\n"%(Anum,Gptr))
	f.write("TERRAIN(%s),\n"%("col_"+id+hex(area.col)))
	f.write("SET_BACKGROUND_MUSIC(0,%d),\n"%area.music)
	f.write("TERRAIN_TYPE(%d),\n"%(area.terrain))
	f.write("JUMP_LINK(local_objects_%s),\nJUMP_LINK(local_warps_%s),\n"%(id,id))
	f.write("END_AREA(),\nRETURN()\n};\n")
	asobj = 'const LevelScript local_objects_%s[]'%id
	f.write(asobj+' = {\n')
	s.MakeDec(asobj)
	#write objects
	for o in area.objects:
		f.write("OBJECT_WITH_ACTS({},{},{},{},{},{},{},{},{},{}),\n".format(*o))
	f.write("RETURN()\n};\n")
	aswarps = 'const LevelScript local_warps_%s[]'%id
	f.write(aswarps+' = {\n')
	s.MakeDec(aswarps)
	#write warps
	for w in area.warps:
		f.write("WARP_NODE({},{},{},{},{}),\n".format(*w))
	f.write("RETURN()\n};\n")

def GrabOGDatH(q,rootdir,name):
	dir = rootdir/'originals'/name
	head = open(dir/'header.h','r')
	head = head.readlines()
	for l in head:
		if not l.startswith('extern'):
			continue
		if 'LevelScript' in l or 'Collision %s_seg7_area'%name in l or 'Collision %s_seg7_collision_level'%name in l:
			continue
		q.write(l)
	return q

def GrabOGDatld(L,rootdir,name):
	dir = rootdir/'originals'/name
	ld = open(dir/'leveldata.c','r')
	ld = ld.readlines()
	grabbed = []
	for l in ld:
		if not l.startswith('#include "levels/%s/'%name):
			continue
		#mem bloat but makes up for mov tex being dumb
		# if ('/areas/' in l and '/model.inc.c' in l):
			# continue
		#for the specific case of levels without subfolders
		q = l.split('/')
		if len(q)>4:
			if ('areas' in q[2] and 'model.inc.c' in q[4]):
				continue
		#I want to include static objects in collision
		# if ('/areas/' in l and '/collision.inc.c' in l):
			# continue
		L.write(l)
		grabbed.append(l)
	return [L,grabbed]

def WriteLevel(rom,s,num,areas,rootdir,m64dir,AllWaterBoxes,Onlys,romname,m64s,seqNums,MusicExtend):
	#create level directory
	WaterOnly = Onlys[0]
	ObjectOnly = Onlys[1]
	MusicOnly = Onlys[2]
	OnlySkip = any(Onlys)
	name=Num2Name[num]
	level=Path(sys.path[0])/("%s"%name)
	if os.path.isdir(level):
		shutil.rmtree(level)
	original = rootdir/'originals'/("%s"%name)
	shutil.copytree(original,level)
	# level.mkdir(exist_ok=True)
	Areasdir = level/"areas"
	Areasdir.mkdir(exist_ok=True)
	#create area directory for each area
	envfx = 0
	for a in areas:
		#area dir
		adir = Areasdir/("%d"%a)
		adir.mkdir(exist_ok=True)
		area=s.levels[num][a]
		Arom = area.rom
		if area.music and not (ObjectOnly or WaterOnly):
			[m64,seqNum] = RipSequence(Arom,area.music,m64dir,num,a,romname,MusicExtend)
			if m64 not in m64s:
				m64s.append(m64)
				seqNums.append(seqNum)
		#get real bank 0x0e location
		s.RME(a,Arom)
		id = name+"_"+str(a)+"_"
		(geo,dls,WB,vfx)=GW.GeoParse(Arom,s.B2P(area.geo),s,area.geo,id)
		#deal with some areas having it vs others not
		if vfx:
			envfx = 1
		if not OnlySkip:
			GW.GeoWrite(geo,adir/"geo.inc.c",id)
			for g in geo:
				s.MakeDec("const GeoLayout Geo_%s[]"%(id+hex(g[1])))
		if not OnlySkip:
			dls = WriteModel(Arom,dls,s,adir,"%s_%d"%(name.upper(),a),id,level)
			for d in dls:
				s.MakeDec("const Gfx DL_%s[]"%(id+hex(d[1])))
		#write collision file
		if not OnlySkip:
			ColParse.ColWrite(adir/"collision.inc.c",s,Arom,area.col,id)
		s.MakeDec('const Collision col_%s[]'%(id+hex(area.col)))
		#write mov tex file
		if not (ObjectOnly or MusicOnly):
			#WB = [types][array of type][box data]
			MovTex = adir / "movtextNew.inc.c"
			MovTex = open(MovTex,'w')
			Wrefs = []
			for k,Boxes in enumerate(WB):
				wref = []
				for j,box in enumerate(Boxes):
					#Now a box is an array of all the data
					#Movtex is just an s16 array, it uses macros but
					#they don't matter
					dat = repr(box).replace("[","{").replace("]","}")
					dat = "static Movtex %sMovtex_%d_%d[] = "%(id,j,k) + dat+";\n\n"
					MovTex.write(dat)
					wref.append("%sMovtex_%d_%d"%(id,k,j))
				Wrefs.append(wref)
			for j,Type in enumerate(Wrefs):
				MovTex.write("const struct MovtexQuadCollection %sMovtex_%d[] = {\n"%(id,j))
				for k,ref in enumerate(Type):
					MovTex.write("{%d,%s},\n"%(k,ref))
				MovTex.write("{-1, NULL},\n};")
				s.MakeDec("struct MovtexQuadCollection %sMovtex_%d[]"%(id,j))
				AllWaterBoxes.append(["%sMovtex_%d"%(id,j),num,a,j])
		print('finished area '+str(a)+ ' in level '+name)
	#now write level script
	if not (WaterOnly or MusicOnly):
		WriteLevelScript(level/"script.c",name,s,s.levels[num],areas,envfx)
	s.MakeDec("const LevelScript level_%s_entry[]"%name)
	if not OnlySkip:
		#finally write header
		H=level/"header.h"
		q = open(H,'w')
		headgaurd="%s_HEADER_H"%(name.upper())
		q.write('#ifndef %s\n#define %s\n#include "types.h"\n#include "game/moving_texture.h"\n'%(headgaurd,headgaurd))
		for h in s.header:
			q.write('extern '+h+';\n')
		#now include externs from stuff in original level
		q = GrabOGDatH(q,rootdir,name)
		q.write("#endif")
		q.close()
		#append to geo.c, maybe the original works good always??
		G = level/"geo.c"
		g = open(G,'r+')
		geolines = g.readlines()
		for i,a in enumerate(areas):
			geo = '#include "levels/%s/areas/%d/geo.inc.c"\n'%(name,(i+1))
			for l in geolines:
				if geo in l:
					break
			else:
				g.write(geo)
		g.close
		#write leveldata.c
		LD = level/"leveldata.c"
		ld = open(LD,'w')
		ld.write(ldHeader)
		[ld,grabbed] = GrabOGDatld(ld,rootdir,name)
		Ftypes = ['model.inc.c"\n','collision.inc.c"\n']
		for i,a in enumerate(areas):
			ld.write('#include "levels/%s/areas/%d/movtextNew.inc.c"\n'%(name,(i+1)))
			start = '#include "levels/%s/areas/%d/'%(name,(i+1))
			for Ft in Ftypes:
				for l in grabbed:
					if start+Ft in l:
						break
				else:
					ld.write(start+Ft)
		ld.write('#include "levels/%s/textureNew.inc.c"\n'%(name))
		ld.close
	return [AllWaterBoxes,m64s,seqNums]

#dictionary of actions to take based on script cmds
jumps = {
    0:LoadRawJumpPush,
    1:LoadRawJump,
    2:Exit,
    5:JumpRaw,
    6:JumpPush,
    7:Pop,
    11:CondPop,
    12:CondJump,
    0x13:SetLevel,
    0x16:LoadAsm,
    0x17:LoadData,
    0x18:LoadMio0,
    0x1a:LoadMio0Tex,
    0x1f:StartArea,
    0x20:EndArea,
    0x21:LoadPolyF3d,
    0x22:LoadPolyGeo,
    0x24:PlaceObject,
    0x25:PlaceMario,
    0x26:ConnectWarp,
    0x27:PaintingWarp,
    0x28:InstantWarp,
    0x2b:SetMarioDefault,
    0x2e:LoadCol,
    0x2f:LoadRoom,
    0x30:SetDialog,
    0x31:SetTerrain,
    0x36:SetMusic,
    0x37:SetMusic2
}

def RipSequence(rom,seqNum,m64Dir,Lnum,Anum,romname,MusicExtend):
	#audio_dma_copy_immediate loads gSeqFileHeader in audio_init at 0x80319768
	#the line of asm is at 0xD4768 which sets the arg to this
	UPW = (lambda x,y: struct.unpack(">L",x[y:y+4])[0])
	gSeqFileHeader=(UPW(rom,0xD4768)&0xFFFF)<<16 #this is LUI asm cmd
	gSeqFileHeader+=(UPW(rom,0xD4770)&0xFFFF) #this is an addiu asm cmd
	#format is tbl,m64s[]
	#tbl format is [len,offset][]
	gSeqFileOffset = gSeqFileHeader+seqNum*8+4
	len=UPW(rom,gSeqFileOffset+4)
	offset=UPW(rom,gSeqFileOffset)
	m64 = rom[gSeqFileHeader+offset:gSeqFileHeader+offset+len]
	m64File = m64Dir/("{1:02X}_Seq_{0}_custom.m64".format(romname,seqNum+MusicExtend))
	m64Name = "{1:02X}_Seq_{0}_custom".format(romname,seqNum+MusicExtend)
	f = open(m64File,'wb')
	f.write(m64)
	f.close()
	return [m64Name,seqNum+MusicExtend]

SoundBanks = {
	0:"00",
	1:"01_terrain",
	2:"02_water",
	3:"03",
	4:"04",
	5:"05",
	6:"06",
	7:"07",
	8:"08_mario",
	9:"09",
	10:"0A_mario_peach",
	11:"0B",
	12:"0C",
	13:"0D",
	14:"0E",
	15:"0F",
	16:"10",
	17:"11",
	18:"12",
	19:"13",
	20:"14_piranha_music_box",
	21:"15",
	22:"16_course_start",
	23:"17",
	24:"18",
	25:"19",
	26:"1A",
	27:"1B",
	28:"1C_endless_stairs",
	29:"1D_bowser_organ",
	30:"1E",
	31:"1F",
	32:"20",
	33:"21",
	34:"22",
	35:"23",
	36:"24",
	37:"25",
}

def CreateSeqJSON(romname,m64s,rootdir,MusicExtend):
	m64Dir = rootdir/"m64"
	originals = rootdir/"originals"/"sequences.json"
	m64s.sort(key=(lambda x: x[1]))
	origJSON = open(originals,'r')
	origJSON = origJSON.readlines()
	#This is the location of the Bank to Sequence table.
	seqMagic = 0x7f0000
	#format is u8 len banks (always 1), u8 bank. Maintain the comment/bank 0 data of the original sequences.json
	UPB = (lambda x,y: struct.unpack(">B",x[y:y+1])[0])
	UPH = (lambda x,y: struct.unpack(">h",x[y:y+2])[0])
	seqJSON = m64Dir/("{}_Sequences.json".format(romname))
	seqJSON = open(seqJSON,'w')
	seqJSON.write("{\n")
	last = 0
	for m64 in m64s:
		bank = UPH(rom,seqMagic+(m64[1]-MusicExtend)*2)
		bank = UPB(rom,seqMagic+bank+1)
		if MusicExtend:
			seqJSON.write("\t\"{}\": [\"{}\"],\n".format(m64[0],SoundBanks[bank]))
			continue
		#fill in missing sequences
		for i in range(last,m64[1]-1,1):
			seqJSON.write(origJSON[i+3])
		seqJSON.write("\t\"{}\": [\"{}\"],\n".format(m64[0],SoundBanks[bank]))
		if m64[1]<0x23:
			og = origJSON[m64[1]+2]
			og = og.split(":")[0] + ": null,\n"
			seqJSON.write(og)
		last = m64[1]
	seqJSON.write("}")

def AppendAreas(entry,script,Append):
	for rom,offset,editor in Append:
		script.Aoffset = offset
		script.editor = editor
		Arom=open(rom,'rb')
		Arom = Arom.read()
		#get all level data from script
		while(True):
			#parse script until reaching special
			q=PLC(Arom,entry)
			#execute special cmd
			entry = jumps[q[0]](Arom,q,q[3],script)
			#check for end, then loop
			if not entry:
				break
	return script

def ExportLevel(rom,level,assets,editor,Append,AllWaterBoxes,Onlys,romname,m64s,seqNums,MusicExtend):
	#choose level
	s = Script(level)
	s.Seg2(rom)
	entry = 0x108A10
	s = AppendAreas(entry,s,Append)
	s.Aoffset = 0
	s.editor = editor
	#get all level data from script
	while(True):
		#parse script until reaching special
		q=PLC(rom,entry)
		#execute special cmd
		entry = jumps[q[0]](rom,q,q[3],s)
		#check for end, then loop
		if not entry:
			break
	#this tool isn't for exporting vanilla levels
	#so I skip ones that don't have bank 0x19 loaded
	#aka custom levels.
	if not s.banks[0x19] and not Onlys[1]:
		return
	#now area class should have data
	#along with pointers to all models
	rootdir = Path(sys.path[0])
	ass=Path("assets")
	ass=Path(sys.path[0])/ass
	ass.mkdir(exist_ok=True)
	m64dir = rootdir/"m64"
	m64dir.mkdir(exist_ok=True)
	#create subfolders for each model
	if not all(Onlys):
		for i in assets:
			#skip error for now until seg 2 detect
			if s.models[i]:
				md = ass/("%d"%i)
				md.mkdir(exist_ok=True)
				print(i,"model")
				if s.models[i][1]=='geo':
					dls=WriteGeo(rom,s,i,md)
				else:
					dls=[[s.B2P(s.models[i][0]),s.models[i][0]]]
				WriteModel(rom,dls,s,md,"MODEL_%d"%i,"actor_"+str(i)+"_",md)
	#now do level
	return WriteLevel(rom,s,level,s.GetNumAreas(level),rootdir,m64dir,AllWaterBoxes,Onlys,romname,m64s,seqNums,MusicExtend)

TextMap = {
	80:'^',
	81:'|',
	82:'<',
	83:'>',
	0x9e:' ',
	0x9f:'-',
	111:',',
	84:'[A]',
	85:'[B]',
	86:'[C]',
	87:'[Z]',
	88:'[R]',
	208:'/',
	62:"'",
	63:'.',
	224:'[%]',
	225:'(',
	226:')(',
	227:')',
	228:'+',
	228:'↔',
	229:'&',
	230:':',
	240:'゛',
	241:'゜',
	242:'!',
	243:'%',
	244:'?',
	245:'『',
	246:'』',
	247:'~',
	248:'…',
	249:'$',
	250:'★',
	251:'×',
	252:'・',
	253:'☆',
	254:'\\n\\\n',
	209:'the',
	210:'you'
}

Course_Names= {
	0:"COURSE_BOB",
	1:"COURSE_WF",
	2:"COURSE_JRB",
	3:"COURSE_CCM",
	4:"COURSE_BBH",
	5:"COURSE_HMC",
	6:"COURSE_LLL",
	7:"COURSE_SSL",
	8:"COURSE_DDD",
	9:"COURSE_SL",
	10:"COURSE_WDW",
	11:"COURSE_TTM",
	12:"COURSE_THI",
	13:"COURSE_TTC",
	14:"COURSE_RR",
	15:"COURSE_BITDW",
	16:"COURSE_BITFS",
	17:"COURSE_BITS",
	18:"COURSE_PSS",
	19:"COURSE_COTMC",
	20:"COURSE_TOTWC",
	21:"COURSE_VCUTM",
	22:"COURSE_WMOTR",
	23:"COURSE_SA",
	24:"COURSE_CAKE_END"
}


#The locations of the star positions in the following struct, 3*(Type,ROM)
StarPositions = {
'KoopaBoB':('>h',0xEd868,'>h',0xEd86A,'>h',0xEd86C),
'KoopaTHI':('>h',0xEd878,'>h',0xEd87A,'>h',0xEd87C),
}

#**Trajectory. So this is the location of the pointer to the trajectory in the rom
Trajectories = {
'KoopaBoB':0xEd864,
'KoopaTHI':0xEd874
}

#Rip misc data that may or may not need to be ported. This currently is trajectories and star positions.
#Do this if misc or 'all' is called on a rom.
def ExportMisc(rom,rootdir,romname):
	misc = rootdir/'misc'
	misc.mkdir(exist_ok=True)
	StarPos = misc/('%s_StarPositions.inc.c'%romname)
	Trajectory = misc/('%s_Trajectories.inc.c'%romname)
	#Trajectories are by default in the level bank, but moved to vram for all hacks
	#If your trajectory does not follow this scheme, then too bad
	UPA = (lambda x,y,z,w: struct.unpack("%s"%z,x[y:y+w]))
	Trj = open(Trajectory,'w')
	for k,v in Trajectories.items():
		Dat = UPA(rom,v,'>L',4)[0]
		#Check if Dat is in a segment or not
		if Dat>>24!=0x80:
			Trj.write('//%s Has the default vanilla value or an unrecognizable pointer\n\n'%k)
		else:
			Trj.write('const Trajectory {}_path[] = {{\n'.format(k))
			Dat = Dat-0x7F200000
			x=0
			while(True):
				point = UPA(rom,Dat+x,'>4h',8)
				if point[0]==-1:
					break
				Trj.write('\tTRAJECTORY_POS({},{},{},{}),\n'.format(*point))
				x+=8
			Trj.write('\tTRAJECTORY_END(),\n};\n')
	#Star positions



def AsciiConvert(num):
	#numbers start at 0x30
	if num<10:
		return chr(num+0x30)
	#capital letters start at 0x41
	elif num<0x24:
		return chr(num+0x37)
	#lowercase letters start at 0x61
	elif num<0x3E:
		return chr(num+0x3D)
	else:
			return TextMap[num]

#seg 2 is mio0 compressed which means C code doesn't translate to whats in the rom at all.
#This basically means I have to hardcode offsets, it should work for almost every rom anyway.
def ExportText(rom,rootdir,TxtAmt,romname):
	s = Script(9)
	s.Seg2(rom)
	DiaTbl = 0x1311E+s.banks[2][0]
	text = rootdir/"misc"
	text.mkdir(exist_ok=True)
	text = text/("%s_dialogs.h"%romname)
	text = open(text,'w',encoding="utf-8")
	UPW = (lambda x,y: struct.unpack(">L",x[y:y+4])[0])
	#format is u32 unused, u8 lines/box, u8 pad, u16 X, u16 width, u16 pad, offset
	DialogFmt = "int:32,2*uint:8,3*uint:16,uint:32"
	for dialog in range(0,TxtAmt*16,16):
		StrSet = BitArray(rom[DiaTbl+dialog:DiaTbl+16+dialog])
		StrSet = StrSet.unpack(DialogFmt)
		#mio0 compression messes with banks and stuff it just werks
		Mtxt = s.B2P(StrSet[6]+0x3156)
		str = ""
		while(True):
			num = rom[Mtxt:Mtxt+1][0]
			if num!=0xFF:
				str+=AsciiConvert(num)
			else:
				break
			Mtxt+=1
		text.write('DEFINE_DIALOG(DIALOG_{0:03d},{1:d},{2:d},{3:d},{4:d}, _("{5}"))\n\n'.format(int(dialog/16),StrSet[0],StrSet[1],StrSet[3],StrSet[4],str))
	text.close()
	#now do courses
	courses = rootdir/("%s_courses.h"%romname)
	LevelNames = 0x8140BE
	courses = open(courses,'w',encoding="utf-8")
	for course in range(26):
		name = s.B2P(UPW(rom,course*4+LevelNames)+0x3156)
		str = ""
		while(True):
			num = rom[name:name+1][0]
			if num!=0xFF:
				str+=AsciiConvert(num)
			else:
				break
			name+=1
		acts = []
		ActTbl = 0x814A82
		if course<15:
			#get act names
			for act in range(6):
				act = s.B2P(UPW(rom,course*24+ActTbl+act*4)+0x3156)
				Actstr=""
				while(True):
					num = rom[act:act+1][0]
					if num!=0xFF:
						Actstr+=AsciiConvert(num)
					else:
						break
					act+=1
				acts.append(Actstr)
			courses.write("COURSE_ACTS({}, _(\"{}\"),\t_(\"{}\"),\t_(\"{}\"),\t_(\"{}\"),\t_(\"{}\"),\t_(\"{}\"),\t_(\"{}\"))\n\n".format(Course_Names[course],str,*acts))
		elif course<25:
			courses.write("SECRET_STAR({}, _(\"{}\"))\n".format(course,str))
		else:
			courses.write("CASTLE_SECRET_STARS(_(\"{}\"))\n".format(str))
	#do extra text
	Extra = 0x814A82+15*6*4
	for i in range(7):
		Ex=s.B2P(UPW(rom,Extra+i*4)+0x3156)
		str=""
		while(True):
			num = rom[Ex:Ex+1][0]
			if num!=0xFF:
				str+=AsciiConvert(num)
			else:
				break
			Ex+=1
		courses.write("EXTRA_TEXT({},_(\"{}\"))\n".format(i,str))
	courses.close()

def ExportWaterBoxes(AllWaterBoxes,rootdir):
	MovtexEdit = rootdir / "moving_texture.inc.c"
	infoMsg = """#include <ultra64.h>
#include "sm64.h"
#include "moving_texture.h"
#include "area.h"
/*
This is an include meant to help with the addition of moving textures for water boxes. Moving textures are hardcoded in vanilla, but in hacks they're procedural. Every hack uses 0x5000 +Type (0 for water, 1 for toxic mist, 2 for mist) to locate the tables for their water boxes. I will replicate this by using a 3 dimensional array of pointers. This wastes a little bit of memory but is way easier to manage.
To use this, goto your moving_texture.c file and change the default case in void *get_quad_collection_from_id(u32 id) to return GetRomhackWaterBox(id); Then place this file in your source folder so that it can be included.
Make sure you add extern void *GetRomhackWaterBox(u32 id); to moving_texture.h so that you do not get a multiple reference error.
You could also just use the references shown here at the top and and them manually yourself to the current switch case.
*/
"""
	if not AllWaterBoxes:
		print("no water boxes")
		return
	MTinc = open(MovtexEdit,'w')
	MTinc.write(infoMsg)
	for a in AllWaterBoxes:
		MTinc.write("extern u8 "+a[0]+"[];\n")
	MTinc.write("\nstatic void *RM2C_Water_Box_Array[33][8][3] = {\n")
	AreaNull = "{"+"NULL,"*3+"},"
	LevelNull = "{ "+AreaNull*8+" },\n"
	LastL = 4
	LastA = 0
	LastType=0
	first = 0
	for wb in AllWaterBoxes:
		L = wb[1]
		A = wb[2]
		T = wb[3]
		if (A!=LastA or L!=LastL) and first!=0:
			for i in range(2-LastType):
				MTinc.write("NULL,")
			MTinc.write("},")
		if L!=LastL and first!=0:
			LastType = 0
			for i in range(7-LastA):
				MTinc.write(AreaNull)
			LastA = 0
			MTinc.write(" },\n")
		for i in range(L-LastL-1):
			MTinc.write(LevelNull)
		if first==0 or L!=LastL:
			MTinc.write("{ ")
		for i in range(A-LastA):
			MTinc.write(AreaNull)
		for i in range(T-LastType):
			MTinc.write("NULL,")
		if T==0:
			MTinc.write("{")
		MTinc.write("&%s,"%wb[0])
		LastL = L
		LastA = A
		LastType = T
		first=1
	for i in range(2-LastType):
		MTinc.write("NULL,")
	MTinc.write("},")
	for i in range(7-LastA):
		MTinc.write(AreaNull)
	MTinc.write(" }\n};\n")
	func = """
void *GetRomhackWaterBox(u32 id){
id = id&0xF;
return RM2C_Water_Box_Array[gCurrLevelNum-4][gCurrAreaIndex][id];
};"""
	MTinc.write(func)

if __name__=='__main__':
	HelpMsg="""
------------------Invalid Input - Error ------------------

Arguments for RM2C are as follows:
RM2C.py, rom="romname", editor=False, levels=[] (or levels='all'), assets=[] (or assets='all'), Append=[(rom,areaoffset,editor),...] WaterOnly=0 ObjectOnly=0 MusicOnly=0 MusicExtend=0 Text=0 Misc=0

Arguments with equals sign are shown in default state, do not put commas between args.
Levels and assets accept any list argument or only the string 'all'. Append is for when you want to combine multiple roms. The appended roms will be use the levels of the original rom, but use the areas of the appended rom with an offset. You must have at least one level to export assets because the script needs to read the model load cmds to find pointers to data.
The "Only" options are to only export certain things either to deal with specific updates or updates to RM2C itself. Only use one at a time. An only option will not maintain other data. Do not use Append with MusicOnly, it will have no effect.
MusicExtend is for when you want to add in your custom music on top of the original tracks. Set it to the amount you want to offset your tracks by (0x23 for vanilla).

Example input1 (all models in BoB for editor rom):
python RM2C.py rom="ASA.z64" editor=True levels=[9] assets=range(0,255)

Example input2 (Export all Levels in a RM rom):
python RM2C.py rom="baserom.z64" levels='all'

Example input3 (Export all BoB in a RM rom with a second area from another rom):
python RM2C.py rom="baserom.z64" levels='all' Append=[('rom2.z64',1,True)]

NOTE! if you are on unix bash requires you to escape certain characters. For this module, these
are quotes and paranthesis. Add in a escape before each.

example: python3 RM2C.py rom=\'sm74.z64\' levels=[9] Append=[\(\'sm74EE.z64\',1,1\)] editor=1

A bad input will automatically generate an escaped version of your args, but it cannot do so before
certain bash errors.
------------------Invalid Input - Error ------------------
"""
	#set default arguments
	levels=[]
	assets=[]
	editor=False
	rom=''
	Append=[]
	args = ""
	WaterOnly = 0
	ObjectOnly = 0
	MusicOnly = 0
	MusicExtend = 0
	Text = 0
	Misc=0
	#This is not an arg you should edit really
	TxtAmount = 170
	for arg in sys.argv[1:]:
		args+=arg+" "
	a = "\\".join(args)
	a = "python3 RM2C.py "+a
	try:
		#the utmosts of cringes
		for arg in sys.argv:
			if arg=='RM2C.py':
				continue
			arg=arg.split('=')
			locals()[arg[0]]=eval(arg[1])
	except:
		print(HelpMsg)
		print("If you are using terminal try using this\n"+a)
		raise 'bad arguments'
	args = (levels,assets)
	romname = rom.split(".")[0]
	rom=open(rom,'rb')
	rom = rom.read()
	#Export dialogs and course names
	if Text or args[0]=='all':
		for A in Append:
			Aname = A[0].split(".")[0]
			Arom = open(A[0],'rb')
			Arom = Arom.read()
			ExportText(Arom,Path(sys.path[0]),TxtAmount,Aname)
		ExportText(rom,Path(sys.path[0]),TxtAmount,romname)
		print('Text Finished')
		if Text:
			sys.exit(0)
	#Export misc data like trajectories or star positions.
	if Misc or args[0]=='all':
		for A in Append:
			Aname = A[0].split(".")[0]
			Arom = open(A[0],'rb')
			Arom = Arom.read()
			ExportMisc(Arom,Path(sys.path[0]),Aname)
		ExportMisc(rom,Path(sys.path[0]),romname)
		print('Misc Finished')
		if Misc:
			sys.exit(0)
	print('Starting Export')
	AllWaterBoxes = []
	m64s = []
	seqNums = []
	Onlys = [WaterOnly,ObjectOnly,MusicOnly]
	if args[0]=='all':
		for k in Num2Name.keys():
			if args[1]=='all':
				ExportLevel(rom,k,range(1,255,1),editor,Append,AllWaterBoxes,Onlys,romname,m64s,seqNums,MusicExtend)
			else:
				ExportLevel(rom,k,args[1],editor,Append,AllWaterBoxes,Onlys,romname,m64s,seqNums,MusicExtend)
			print(Num2Name[k] + ' done')
	else:
		for k in args[0]:
			if args[1]=='all':
				ExportLevel(rom,k,range(1,255,1),editor,Append,AllWaterBoxes,Onlys,romname,m64s,seqNums,MusicExtend)
			else:
				ExportLevel(rom,k,args[1],editor,Append,AllWaterBoxes,Onlys,romname,m64s,seqNums,MusicExtend)
			print(Num2Name[k] + ' done')
	#AllWaterBoxes should have refs to all water boxes, using that, I will generate a function
	#and array of references so it can be hooked into moving_texture.c
	#example of AllWaterBoxes format [[str,level,area,type]...]
	if not (MusicOnly or ObjectOnly):
		ExportWaterBoxes(AllWaterBoxes,Path(sys.path[0]))
	if not (WaterOnly or ObjectOnly):
		CreateSeqJSON(romname,list(zip(m64s,seqNums)),Path(sys.path[0]),MusicExtend)
	print('Export Completed')