import{r as V}from"./react-vendor-Dm9lbsEx.js";var w={exports:{}},j={},R={exports:{}},h={};/**
 * @license React
 * use-sync-external-store-shim.production.js
 *
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */var s=V;function z(e,u){return e===u&&(e!==0||1/e===1/u)||e!==e&&u!==u}var D=typeof Object.is=="function"?Object.is:z,M=s.useState,O=s.useEffect,p=s.useLayoutEffect,I=s.useDebugValue;function _(e,u){var o=u(),c=M({inst:{value:o,getSnapshot:u}}),r=c[0].inst,n=c[1];return p(function(){r.value=o,r.getSnapshot=u,S(r)&&n({inst:r})},[e,o,u]),O(function(){return S(r)&&n({inst:r}),e(function(){S(r)&&n({inst:r})})},[e]),I(o),o}function S(e){var u=e.getSnapshot;e=e.value;try{var o=u();return!D(e,o)}catch{return!0}}function G(e,u){return u()}var W=typeof window>"u"||typeof window.document>"u"||typeof window.document.createElement>"u"?G:_;h.useSyncExternalStore=s.useSyncExternalStore!==void 0?s.useSyncExternalStore:W;R.exports=h;var L=R.exports;/**
 * @license React
 * use-sync-external-store-shim/with-selector.production.js
 *
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */var y=V,g=L;function k(e,u){return e===u&&(e!==0||1/e===1/u)||e!==e&&u!==u}var C=typeof Object.is=="function"?Object.is:k,U=g.useSyncExternalStore,A=y.useRef,B=y.useEffect,F=y.useMemo,H=y.useDebugValue;j.useSyncExternalStoreWithSelector=function(e,u,o,c,r){var n=A(null);if(n.current===null){var f={hasValue:!1,value:null};n.current=f}else f=n.current;n=F(function(){function d(t){if(!m){if(m=!0,l=t,t=c(t),r!==void 0&&f.hasValue){var a=f.value;if(r(a,t))return v=a}return v=t}if(a=v,C(l,t))return a;var E=c(t);return r!==void 0&&r(a,E)?(l=t,a):(l=t,v=E)}var m=!1,l,v,$=o===void 0?null:o;return[function(){return d(u())},$===null?void 0:function(){return d($())}]},[u,o,c,r]);var i=U(e,n[0],n[1]);return B(function(){f.hasValue=!0,f.value=i},[i]),H(i),i};w.exports=j;var x=w.exports,J={};/**
 * @license React
 * use-sync-external-store-with-selector.production.js
 *
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */var b=V;function K(e,u){return e===u&&(e!==0||1/e===1/u)||e!==e&&u!==u}var N=typeof Object.is=="function"?Object.is:K,P=b.useSyncExternalStore,Q=b.useRef,T=b.useEffect,X=b.useMemo,Y=b.useDebugValue;J.useSyncExternalStoreWithSelector=function(e,u,o,c,r){var n=Q(null);if(n.current===null){var f={hasValue:!1,value:null};n.current=f}else f=n.current;n=X(function(){function d(t){if(!m){if(m=!0,l=t,t=c(t),r!==void 0&&f.hasValue){var a=f.value;if(r(a,t))return v=a}return v=t}if(a=v,N(l,t))return a;var E=c(t);return r!==void 0&&r(a,E)?(l=t,a):(l=t,v=E)}var m=!1,l,v,$=o===void 0?null:o;return[function(){return d(u())},$===null?void 0:function(){return d($())}]},[u,o,c,r]);var i=P(e,n[0],n[1]);return T(function(){f.hasValue=!0,f.value=i},[i]),Y(i),i};export{x as w};
