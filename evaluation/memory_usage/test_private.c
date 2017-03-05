
// #define LIST {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 193, 194, 195, 196, 197, 198, 199, 200, 201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 211, 212, 213, 214, 215, 216, 217, 218, 219, 220, 221, 222, 223, 224, 225, 226, 227, 228, 229, 230, 231, 232, 233, 234, 235, 236, 237, 238, 239, 240, 241, 242, 243, 244, 245, 246, 247, 248, 249, 250, 251, 252, 253, 254, 255, 256, 257, 258, 259, 260, 261, 262, 263, 264, 265, 266, 267, 268, 269, 270, 271, 272, 273, 274, 275, 276, 277, 278, 279, 280, 281, 282, 283, 284, 285, 286, 287, 288, 289, 290, 291, 292, 293, 294, 295, 296, 297, 298, 299, 300, 301, 302, 303, 304, 305, 306, 307, 308, 309, 310, 311, 312, 313, 314, 315, 316, 317, 318, 319, 320, 321, 322, 323, 324, 325, 326, 327, 328, 329, 330, 331, 332, 333, 334, 335, 336, 337, 338, 339, 340, 341, 342, 343, 344, 345, 346, 347, 348, 349}

int calcutate(int index)
{
  int a = (index * 32) & 128;
  return a;
}

__kernel void test(int size, global int* in, global int* out)
{
  int idx = get_global_id(0);
  // out of bound kernel task for padding

  if (idx >= size) {
    return;
  }

  // if the private variable is referenced by global. It's created.
  int ga[8192] = {1};
  __local int bb[1];
  bb[idx%1] = idx;
  barrier(CLK_LOCAL_MEM_FENCE);

  int a1 = idx - 1;
  int a2 = idx + 2;
  int a3 = idx + 3;
  int a4 = idx + 4;
  int a5 = idx + 5;
  int a6 = idx + 6;
  int a7 = idx + 7;
  int a8 = idx + 8;
  int a9 = idx + 9;
  int a10 = idx + 10;
  int a11 = idx - 10;
  int a12 = idx + 11;
  int a13 = idx - 12;
  int a14 = idx + 13;
  int a15 = idx - 14;
  int a16 = idx + 15;
  int a17 = idx - 16;
  int a18 = idx + 17;
  int a19 = idx - 18;
  int a20 = idx + 19;

  int a21 = idx - 20;
  int a22 = idx + 21;
  int a23 = idx - 22;
  int a24 = idx + 23;
  int a25 = idx - 24;
  int a26 = idx + 25;
  int a27 = idx - 26;
  int a28 = idx + 27;
  int a29 = idx - 28;
  int a30 = idx + 29;

  int a31 = idx + 30;
  int a32 = idx - 31;
  int a33 = idx + 32;
  int a34 = idx - 33;
  int a35 = idx + 34;
  int a36 = idx - 35;
  int a37 = idx + 36;
  int a38 = idx - 37;
  int a39 = idx + 38;
  int a40 = idx - 39;

  int a41 = idx + 40;
  int a42 = idx - 41;
  int a43 = idx + 42;
  int a44 = idx - 43;
  int a45 = idx + 44;
  int a46 = idx - 45;
  int a47 = idx + 46;
  int a48 = idx - 47;
  int a49 = idx + 48;
  int a50 = idx - 49;

  int a51 = idx + 50;
  int a52 = idx - 51;
  int a53 = idx + 52;
  int a54 = idx - 53;
  int a55 = idx + 54;
  int a56 = idx - 55;
  int a57 = idx + 56;
  int a58 = idx - 57;
  int a59 = idx + 58;
  int a60 = idx - 59;

  int a61 = idx - 60;
  int a62 = idx + 61;
  int a63 = idx - 62;
  int a64 = idx + 63;
  int a65 = idx - 64;
  int a66 = idx + 65;
  int a67 = idx - 66;
  int a68 = idx + 67;
  int a69 = idx - 68;
  int a70 = idx + 69;

  int a71 = idx - 70;
  int a72 = idx + 71;
  int a73 = idx - 72;
  int a74 = idx + 73;
  int a75 = idx - 74;
  int a76 = idx + 75;
  int a77 = idx - 76;
  int a78 = idx + 77;
  int a79 = idx - 78;
  int a80 = idx + 79;

  int a81 = idx + 80;
  int a82 = idx - 81;
  int a83 = idx + 82;
  int a84 = idx - 83;
  int a85 = idx + 84;
  int a86 = idx - 85;
  int a87 = idx + 86;
  int a88 = idx - 87;
  int a89 = idx + 88;
  int a90 = idx - 99;

  int a91 = idx + 90;
  int a92 = idx - 91;
  int a93 = idx + 92;
  int a94 = idx - 93;
  int a95 = idx + 94;
  int a96 = idx - 95;
  int a97 = idx + 96;
  int a98 = idx - 97;
  int a99 = idx + 98;
  int a100 = idx - 99;

  // int xx = a1 * a2 / a3 * a4 * a5 / a6 / a7 * a8 + a9 * a10;
  // xx +
  out[idx] = a1 +  a2 *  a3 +  a4 +  a5 +  a6 +  a7 +  a8 +  a9 - a10 +\
             a11 + a12 + a13 + a14 + a15 + a16 + a17 - a18 + a19 * a20 +\
             a21 * a22 + a23 + a24 * a25 + a26 - a27 + a28 + a29 + a30 +\
             a31 + a32 + a33 / a34 + a35 - a36 + a37 + a38 * a39 + a40 +\
             a41 / a42 + a43 + a44 - a45 * a46 + a47 + a48 + a49 + a50 +\
             a51 + a52 + a53 - a54 + a55 + a56 + a57 + a58 / a59 + a60 +\
             a61 + a62 - a63 + a64 + a65 * a66 + a67 + a68 + a69 + a70 +\
             a71 - a72 + a73 + a74 / a75 + a76 / a77 * a78 + a79 + a80 +\
             a81 - a82 + a83 + a84 + a85 + a86 + a87 + a88 + a89 + a90 +\
             a91 - a92 + a93 + a94 + a95 + a96 + a97 + a98 + a99 + a100 + ga[idx%bb[idx]];
}
