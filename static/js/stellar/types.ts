import type { EasingName } from "./easing";

export type CSSPropValue = string | number | boolean;
export type CSSProps = Record<string, CSSPropValue | { [key: string]: CSSPropValue | CSSProps }>;

export type ParametricValue = {
    steps: number[]
    values: number[]
    easings?: EasingName | EasingName[]
    decimals?: number | number[]
    prefix?: string | string[]
    suffix?: string | string[]
    static?: StaticProps
    namedKeys?: boolean // use clothes sizing instead of numbers
}

export type ParametricValueRange = {
    steps: number[]
    values: number[][]
    easings?: EasingName | EasingName[]
    decimals?: number | number[]
    prefix?: string | string[]
    suffix?: string | string[]
    delimiter?: string
    outerPrefix?: string
    outerSuffix?: string
    static?: StaticProps
    namedKeys?: boolean // use clothes sizing instead of numbers
}

export type NamedParametricValueRange = {
    names: { [name: string]: number },
} & ParametricValueRange

export type StaticProps = Record<string, string | number | boolean | { [key: string]: StaticProps }>

export type PrefixSuffix = {
    prefix?: string
    suffix?: string
}

export type KeyFrameValue = number[] | {
    prefix?: string
    suffix?: string
    values: ((number | number[])[]) | Record<string, KeyFrameValue>
}
export type KeyFrameValues = Record<string, KeyFrameValue>

export type AnimationKeyframeConfig = {
    type: 'from' | 'to'
    values: KeyFrameValues
} | {
    type: '%'
    steps: number[],
    values: KeyFrameValues
    mediaQueries?: Record<string, Record<string, KeyFrameValue>>
}

export type AnimationConfig = Record<string, number | {
    durationStep: number
    easing?: EasingName
    doesLoop?: boolean
}>
export type AnimationKeyframesConfig = Record<string, AnimationKeyframeConfig>

export type Config = {
    animations: {
        values: AnimationConfig
        keyframes: AnimationKeyframesConfig
    },
    aspectRatios: {
        [name: string]: number
    },
    easings: {
        steps: number
        simplifyTolerance: number
    },
    borders: {
        size: ParametricValue
        radius: ParametricValue
        radiusConditional: ParametricValue
    },
    colors: {
        [name: string]: ParametricValueRange
    },
    customMedia: Record<string, string>
    durations: ParametricValue
    fonts: {
        noInjection: boolean
        families: StaticProps
        weights: ParametricValue
        lineHeights: ParametricValue
        letterSpacing: ParametricValue
        size: ParametricValue
        sizeFluid: ParametricValueRange
    },
    gradients: {
        stops: number
    },
    size: {
        base: ParametricValue,
        px: ParametricValue,
        fluid: ParametricValueRange,
        content: ParametricValue,
        header: ParametricValue,
        viewport: ParametricValue,
        relative: ParametricValue,
    }
    zIndex: ParametricValue,
}