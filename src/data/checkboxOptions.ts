// 忌口选项配置
export const ALLERGY_OPTIONS = [
  {
    id: 'seafood',
    label: '海鲜类',
    image: require('../../assets/allergies/海鲜类.png'),
  },
  {
    id: 'nuts',
    label: '坚果类', 
    image: require('../../assets/allergies/坚果类.png'),
  },
  {
    id: 'eggs',
    label: '蛋类',
    image: require('../../assets/allergies/蛋类.png'),
  },
  {
    id: 'soy',
    label: '大豆类',
    image: require('../../assets/allergies/大豆类.png'),
  },
  {
    id: 'dairy',
    label: '乳制品类',
    image: require('../../assets/allergies/乳制品类.png'),
  },
  {
    id: 'other-allergy',
    label: '其他',
    image: require('../../assets/food/其他.png'),
  },
  
];

// 偏好选项配置
export const PREFERENCE_OPTIONS = [
  {
    id: 'spicy',
    label: '香辣',
    image: require('../../assets/preferences/香辣.png'),
  },
  {
    id: 'mild',
    label: '清淡',
    image: require('../../assets/preferences/清淡.png'),
  },
  {
    id: 'sweet',
    label: '甜口',
    image: require('../../assets/preferences/甜口.png'),
  },
  {
    id: 'sour-spicy',
    label: '酸辣',
    image: require('../../assets/preferences/酸辣.png'),
  },
  {
    id: 'salty',
    label: '咸鲜',
    image: require('../../assets/preferences/咸鲜.png'),
  },
  {
    id: 'other-preference',
    label: '其他',
    image: require('../../assets/food/其他.png'),
  },
];

// 食物类型选项配置
export const FOOD_TYPE_OPTIONS = [
  {
    id: 'meal',
    label: '吃饭',
    image: require('../../assets/food/美食.png'),
  },
  {
    id: 'drink',
    label: '喝奶茶',
    image: require('../../assets/food/饮品.png'),
  },
];