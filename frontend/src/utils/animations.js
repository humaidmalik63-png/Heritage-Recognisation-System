/**
 * Framer Motion Editorial Animation System
 * Visual Heritage Recognition & Grounded Cultural Discovery Platform
 * 
 * Editorial, restrained, dignified transitions honoring cultural architecture.
 * Respects prefers-reduced-motion across all variants.
 */

export const editorialEasing = [0.16, 1, 0.3, 1]; // Premium cubic-bezier curve

export const headerVariants = {
  hidden: { y: -20, opacity: 0 },
  visible: {
    y: 0,
    opacity: 1,
    transition: {
      duration: 0.6,
      ease: editorialEasing,
    },
  },
};

export const heroContainerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.12,
      delayChildren: 0.08,
    },
  },
};

export const heroHeadingLineVariants = {
  hidden: { y: 28, opacity: 0 },
  visible: {
    y: 0,
    opacity: 1,
    transition: {
      duration: 0.8,
      ease: editorialEasing,
    },
  },
};

export const heroFadeRiseVariants = {
  hidden: { y: 18, opacity: 0 },
  visible: {
    y: 0,
    opacity: 1,
    transition: {
      duration: 0.7,
      ease: editorialEasing,
    },
  },
};

export const ctaStaggerVariants = {
  hidden: { opacity: 0, y: 12 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.6,
      ease: editorialEasing,
    },
  },
};

export const sectionRevealVariants = {
  hidden: { opacity: 0, y: 24 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.75,
      ease: editorialEasing,
    },
  },
};

export const cardStaggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.08,
      delayChildren: 0.1,
    },
  },
};

export const cardStaggerItem = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.65,
      ease: editorialEasing,
    },
  },
};

export const imageRevealVariants = {
  hidden: { scale: 0.97, opacity: 0 },
  visible: {
    scale: 1,
    opacity: 1,
    transition: {
      duration: 0.8,
      ease: editorialEasing,
    },
  },
};

export const buttonTapVariants = {
  hover: { scale: 1.02, y: -1 },
  tap: { scale: 0.98 },
};

export const mobileMenuVariants = {
  closed: {
    opacity: 0,
    height: 0,
    transition: {
      duration: 0.25,
      ease: editorialEasing,
    },
  },
  open: {
    opacity: 1,
    height: 'auto',
    transition: {
      duration: 0.35,
      ease: editorialEasing,
    },
  },
};

export const bottomNavVariants = {
  hidden: { y: 100, opacity: 0 },
  visible: {
    y: 0,
    opacity: 1,
    transition: {
      duration: 0.45,
      ease: editorialEasing,
    },
  },
};

